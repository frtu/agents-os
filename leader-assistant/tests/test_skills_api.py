"""Tests for skill import & discovery (feature 005-skill-import).

Offline and deterministic: the ``skills_library`` fixture (conftest) points
``LEADER_SKILLS_SOURCE`` at a throwaway library of fake ``<name>/SKILL.md`` folders, so
these tests never depend on the real shared library. Covers the available catalog,
plan-first chat import + approve, the traversal guard, idempotence, and REST parity for
the three skill routes.
"""

from __future__ import annotations

import os

import pytest

from app import capabilities


def _make_workspace(client, name="demo"):
    assert capabilities.create_workspace(name).scaffolded
    return name


def _approve(client, risk):
    """Answer a 409's approval card on the existing 008 route (spec 011 FR-25)."""
    return client.post(
        "/api/chat/interaction",
        json={
            "workspace": risk.get("workspace") or None,
            "conversation_id": risk["conversation_id"],
            "interaction_id": risk["interaction_id"],
            "choice": "approve",
        },
    ).json()


def test_catalog_lists_library_skills(client):
    # FR-2: the catalog lists the library's skills with name + description + installed flag.
    v = _make_workspace(client)
    r = client.get("/api/skills", params={"workspace": v})
    assert r.status_code == 200
    body = r.json()
    by_name = {s["name"]: s for s in body["skills"]}
    assert {"weekly-digest", "triage"} <= set(by_name)
    assert by_name["weekly-digest"]["description"] == "Summarise the week"
    assert by_name["weekly-digest"]["installed"] is False


def test_rest_import_asks_before_installing(client, isolated_workspace_root):
    # spec 011 AC-9/AC-17: installing a skill is approval-tier, so at cold start REST asks rather
    # than installing — and nothing is on disk while the question is outstanding.
    v = _make_workspace(client)
    r = client.post("/api/skills/import", json={"workspace": v, "name": "weekly-digest"})
    assert r.status_code == 409
    risk = r.json()
    assert risk["gating"]["name"] == "import_skill"
    assert risk["gating"]["target"] == "weekly-digest"
    assert "PRIVILEGE_GRANTING" in risk["gating"]["modifiers"]  # spec 011 FR-8
    assert not (isolated_workspace_root / v / "skills" / "weekly-digest").exists()


def test_import_report_shape(client):
    # FR-5/FR-7: the report names the created reference-link and records the commit.
    v = _make_workspace(client)
    report = capabilities.import_skill(v, "weekly-digest")
    assert report.name == "weekly-digest"
    assert report.link_path == "skills/weekly-digest"
    assert report.committed is True


def test_rest_import_creates_both_symlinks_and_commits(client, isolated_workspace_root):
    # FR-5/FR-7: an approved import creates skills/<name> AND .claude/skills/<name> links to the
    # source, and the skill then appears in the installed list.
    v = _make_workspace(client)
    risk = client.post("/api/skills/import", json={"workspace": v, "name": "weekly-digest"}).json()
    assert _approve(client, risk)["executed"] is True

    ws = isolated_workspace_root / v
    canonical = ws / "skills" / "weekly-digest"
    mirror = ws / ".claude" / "skills" / "weekly-digest"
    assert canonical.is_symlink() and mirror.is_symlink()
    # Both resolve to the same library skill folder (with its SKILL.md).
    assert (canonical / "SKILL.md").is_file() and (mirror / "SKILL.md").is_file()
    assert canonical.resolve() == mirror.resolve()

    installed = client.get("/api/skills/installed", params={"workspace": v}).json()
    assert "weekly-digest" in installed["skills"]
    # The catalog now marks it installed.
    cat = client.get("/api/skills", params={"workspace": v}).json()
    assert next(s for s in cat["skills"] if s["name"] == "weekly-digest")["installed"] is True


def test_import_is_idempotent(client):
    # FR-5: re-importing an installed skill succeeds without error or duplication. Idempotence is a
    # property of the capability, so it is exercised there rather than through two approval rounds.
    v = _make_workspace(client)
    capabilities.import_skill(v, "triage")
    capabilities.import_skill(v, "triage")
    installed = client.get("/api/skills/installed", params={"workspace": v}).json()["skills"]
    assert installed.count("triage") == 1


def test_unknown_skill_is_rejected(client):
    # FR-6: a name not in the library is rejected with no side effects.
    v = _make_workspace(client)
    r = client.post("/api/skills/import", json={"workspace": v, "name": "does-not-exist"})
    assert r.status_code == 400
    assert client.get("/api/skills/installed", params={"workspace": v}).json()["skills"] == []


def test_traversal_name_is_rejected(client, isolated_workspace_root):
    # FR-6: a path-traversal name cannot escape the workspace's skills/ dir.
    v = _make_workspace(client)
    r = client.post("/api/skills/import", json={"workspace": v, "name": "../evil"})
    assert r.status_code == 400
    assert not (isolated_workspace_root / v / "skills" / "evil").exists()


def test_chat_import_is_plan_first_then_approve(client, offline_agent, isolated_workspace_root):
    # FR-4: "install the <name> skill" returns a pending plan and installs nothing;
    # approving it creates the reference-links.
    v = _make_workspace(client)
    first = client.post(
        "/api/chat", json={"workspace": v, "message": "install the weekly-digest skill"}
    ).json()
    assert first["pending_plan"] is not None
    assert first["executed"] is False
    assert not (isolated_workspace_root / v / "skills" / "weekly-digest").exists()

    cid = first["conversation_id"]
    approved = client.post(
        "/api/chat", json={"workspace": v, "message": "approve", "conversation_id": cid, "approve": True}
    ).json()
    assert approved["executed"] is True
    assert (isolated_workspace_root / v / "skills" / "weekly-digest").is_symlink()
    assert (isolated_workspace_root / v / ".claude" / "skills" / "weekly-digest").is_symlink()


def test_skill_routes_are_registered(client):
    # FR-11 / P9: every skill capability is reachable via a /api/* REST route.
    from app.api import app

    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/api/skills" in paths
    assert "/api/skills/installed" in paths
    assert "/api/skills/import" in paths


@pytest.mark.skipif(
    not os.getenv("LEADER_LIVE_AGENT"),
    reason="requires the claude CLI / credentials; set LEADER_LIVE_AGENT=1 to run",
)
def test_live_agent_discovers_and_runs_imported_skill(client):
    # FR-8/FR-9: after import, a subsequent chat turn can discover and run the skill
    # with no restart. Dynamic load + run can only be exercised with real credentials.
    v = _make_workspace(client)
    assert client.post("/api/skills/import", json={"workspace": v, "name": "weekly-digest"}).status_code == 200
    r = client.post(
        "/api/chat",
        json={"workspace": v, "message": "Use the weekly-digest skill and tell me what it does."},
    )
    assert r.status_code == 200
    assert r.json()["reply"]
