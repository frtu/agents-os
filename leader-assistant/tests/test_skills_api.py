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


def _make_workspace(client, name="demo"):
    assert client.post("/api/workspaces", json={"name": name}).status_code == 200
    return name


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


def test_rest_import_creates_both_symlinks_and_commits(client, isolated_workspace_root):
    # FR-5/FR-7: import creates skills/<name> AND .claude/skills/<name> links to the source,
    # commits to git, and the skill then appears in the installed list.
    v = _make_workspace(client)
    r = client.post("/api/skills/import", json={"workspace": v, "name": "weekly-digest"})
    assert r.status_code == 200
    report = r.json()
    assert report["name"] == "weekly-digest"
    assert report["link_path"] == "skills/weekly-digest"
    assert report["committed"] is True

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
    # FR-5: re-importing an installed skill succeeds without error or duplication.
    v = _make_workspace(client)
    assert client.post("/api/skills/import", json={"workspace": v, "name": "triage"}).status_code == 200
    again = client.post("/api/skills/import", json={"workspace": v, "name": "triage"})
    assert again.status_code == 200
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
