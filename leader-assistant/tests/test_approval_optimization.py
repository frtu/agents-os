"""Feature 009 — approval & clarification optimization (AC-1..AC-10).

Drives the app over HTTP like the rest of the suite. The theme: the approval gate must fire
on a **real, executable, approval-tier effect** and nothing else — never on the words in a
request, and never for an action this build cannot perform.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from app import capabilities


def sse_events(text: str) -> list[dict]:
    return [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]


def _git(workspace, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(workspace), *args], capture_output=True, text=True, check=True
    )
    return out.stdout


# --- AC-1: former trigger words no longer gate ------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "create a summary of the auth concept",
        "merge these two ideas into one note",
        "rename this concept to something clearer",
        "delete the onboarding spec",
        "create a pre interview eval for candidate Jonathan Ryadi from raw/candidates",
    ],
)
def test_ac1_trigger_words_do_not_raise_approval(client, offline_agent, message):
    # AC-1 / FR-2 / FR-3: a word in the message never gates a turn — only a real effect does.
    body = client.post("/api/chat", json={"message": message}).json()
    assert body["pending_plan"] is None
    assert (body["interaction"] or {}).get("kind") != "approval"


def test_ac1_plan_capability_reports_no_action_as_safe(client):
    # AC-1 / FR-4: `plan` itself must not invent risk for a request with no executable action.
    body = client.post("/api/plan", json={"request": "delete the onboarding spec"}).json()
    assert body["risk"] == "safe"
    assert body["requires_approval"] is False
    assert body["capability"] == ""


# --- AC-2: auto/reversible run unprompted; reversible stays undoable --------


def test_ac2_effect_tiers_are_data_declared():
    # AC-2 / FR-1: the risk rules are a data table of declared effect tiers (P12).
    from app import capabilities

    assert capabilities.EFFECTS["query"].tier == "auto"
    assert capabilities.EFFECTS["ingest"].tier == "reversible"
    assert capabilities.EFFECTS["create_workspace"].tier == "approval"
    assert all(e.tier in ("auto", "reversible", "approval") for e in capabilities.EFFECTS.values())


def test_ac2_reversible_ingest_runs_unprompted_and_is_committed(client, isolated_workspace_root):
    # AC-2 / FR-6: a reversible mutation happens immediately, is logged, and is git-committed.
    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"

    r = client.post(
        "/api/ingest",
        json={"workspace": "demo", "title": "Auth notes", "content": "we chose OIDC", "provenance": "notes"},
    )
    assert r.status_code == 200
    assert r.json()["committed"] is True

    log = (workspace / "vault" / "wiki" / "log.md").read_text(encoding="utf-8")
    assert "Auth notes" in log
    assert _git(workspace, "status", "--porcelain").strip() == ""
    assert len(_git(workspace, "log", "--oneline").strip().splitlines()) >= 2


def test_ac2_turn_writes_are_logged_and_committed(client, isolated_workspace_root, monkeypatch):
    # AC-2 / FR-6: wiki pages a turn's skills write are recoverable — the turn leaves a log
    # entry and a commit, which is what makes running them unprompted safe.
    from app import agent

    capabilities.create_workspace("demo")
    workspace = isolated_workspace_root / "demo"
    log_path = workspace / "vault" / "wiki" / "log.md"
    commits_before = len(_git(workspace, "log", "--oneline").strip().splitlines())

    async def _writes_a_page(_prompt, _message, _selector, wpath, sid, _citations, *_a, **_kw):
        (wpath / "vault" / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
        (wpath / "vault" / "wiki" / "concepts" / "oidc.md").write_text("# OIDC\n", encoding="utf-8")
        yield "Captured the OIDC concept.", sid

    monkeypatch.setattr(agent, "run_stream", _writes_a_page)

    body = client.post("/api/chat", json={"workspace": "demo", "message": "note the OIDC concept"}).json()
    assert body["pending_plan"] is None  # reversible work is never gated

    assert "note the OIDC concept" in log_path.read_text(encoding="utf-8")
    assert _git(workspace, "status", "--porcelain").strip() == ""
    assert len(_git(workspace, "log", "--oneline").strip().splitlines()) > commits_before


# --- AC-3: a real plan, and approving executes that exact action -----------


def test_ac3_real_plan_and_approve_executes(client, offline_agent, isolated_workspace_root):
    # AC-3 / FR-5 / FR-13: the plan names the actual capability, target and undo path, and
    # approving runs exactly that action.
    r = client.post("/api/chat", json={"message": "create a workspace named archive"})
    body = r.json()
    plan = body["pending_plan"]
    assert plan is not None
    assert plan["capability"] == "create_workspace"
    assert plan["target"] == "archive"
    assert plan["effect_tier"] == "approval"
    assert plan["reversibility"]
    assert "archive" in body["reply"]
    assert not (isolated_workspace_root / "archive").exists()

    approved = client.post(
        "/api/chat",
        json={"message": "", "conversation_id": body["conversation_id"], "approve": True},
    ).json()
    assert approved["executed"] is True
    assert (isolated_workspace_root / "archive").is_dir()
    assert approved["pending_plan"] is None


def test_ac3_approving_clears_the_pending_plan(client, offline_agent):
    # AC-3 / FR-13: the stored plan is cleared, so a second approve finds nothing pending.
    # spec 011 FR-25 rewords the refusal — `approve=true` is now sugar for answering the card, so
    # "nothing awaiting your approval" is the same fact stated in the card's vocabulary.
    cid = client.post("/api/chat", json={"message": "create a workspace named once"}).json()[
        "conversation_id"
    ]
    first = client.post(
        "/api/chat", json={"message": "", "conversation_id": cid, "approve": True}
    ).json()
    assert first["executed"] is True
    again = client.post("/api/chat", json={"message": "", "conversation_id": cid, "approve": True}).json()
    assert again["executed"] is False
    assert "nothing awaiting your approval" in again["reply"].lower()


# --- AC-4: no dead-ends ----------------------------------------------------


def test_ac4_non_executable_request_answers_without_a_plan(client, offline_agent):
    # AC-4 / FR-4: no plan, no approval, and the dead-end string is gone for good.
    body = client.post("/api/chat", json={"message": "deploy to prod"}).json()
    assert body["pending_plan"] is None
    assert body["executed"] is False
    assert body["reply"]
    assert "isn't automatable yet" not in body["reply"]


def test_ac4_dead_end_message_is_absent_from_the_codebase():
    # AC-4 / FR-4: the dead-end branch is deleted, not merely unreachable.
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "app" / "capabilities.py"
    assert "isn't automatable yet" not in src.read_text(encoding="utf-8")


def test_ac4_stale_pending_plan_clears_without_a_dead_end(client, offline_agent):
    # AC-4 / FR-4: a plan stored by an older build (no executor) resolves cleanly on approve
    # instead of parking forever. Reproduces the reported session bug.
    from app import conversation, vault

    cid = client.post("/api/chat", json={"message": "hello"}).json()["conversation_id"]
    workspace = vault.resolve_workspace(None)
    conv = conversation.load(workspace, cid)
    conversation.set_pending_plan(
        conv,
        "create a pre interview eval for candidate Jonathan Ryadi from raw/candidates",
        {"workspace": workspace.name, "request": "create a pre interview eval", "steps": [],
         "risk": "risky", "requires_approval": True},
    )

    body = client.post("/api/chat", json={"message": "", "conversation_id": cid, "approve": True}).json()
    assert "isn't automatable yet" not in body["reply"]
    assert body["pending_plan"] is None
    assert conversation.load(workspace, cid).pending_plan is None


def test_ac4_stale_pending_plan_is_dropped_on_the_next_turn(client, offline_agent):
    # AC-4 / FR-4: a dead plan from an older build must not re-present its card forever — the
    # next ordinary turn discards it instead of re-raising an approval nothing can honor.
    from app import conversation, vault

    cid = client.post("/api/chat", json={"message": "hello"}).json()["conversation_id"]
    workspace = vault.resolve_workspace(None)
    conversation.set_pending_plan(
        conversation.load(workspace, cid),
        "create a pre interview eval for candidate Jonathan Ryadi from raw/candidates",
        {"workspace": workspace.name, "request": "create a pre interview eval", "steps": [],
         "risk": "risky", "requires_approval": True},
    )

    body = client.post(
        "/api/chat", json={"message": "what did we decide?", "conversation_id": cid}
    ).json()
    assert body["pending_plan"] is None
    assert conversation.load(workspace, cid).pending_plan is None
    assert client.get(
        "/api/chat/interaction", params={"conversation_id": cid}
    ).json() is None


# --- AC-5 / AC-6 / AC-7: the escape hatch ---------------------------------


def _seed_experience(operation_name: str = "seeded", samples: int = 1) -> None:
    """Put prior decisions in the experience store so a turn is no longer cold start (011 FR-20).

    Cold start is checked before anything else in the grant filter, so without this **every** gated
    turn asks and trust mode is unobservable. The seeded fingerprint is deliberately unrelated to the
    operation under test, so the store is non-empty without conferring precedent on it.
    """
    from app import experience
    from app.execution_gate import Operation

    for i in range(samples):
        assert experience.record(
            run_id=f"seed-{operation_name}-{i}",
            operation=Operation(
                kind="capability",
                name=operation_name,
                target="somewhere",
                tier="approval",
                reversibility="git revert",
            ),
            decision="approve",
            source="user",
            score=4,
        )


def test_ac5_trust_mode_grants_a_gated_action_without_prompting(
    client, offline_agent, isolated_workspace_root, monkeypatch
):
    # AC-5 / FR-7, as bounded by spec 011 FR-17: standing consent is what lets the judge's `approve`
    # be honoured, so the action runs with no card. Cold start and the precedent-free ceiling are
    # lifted here so trust mode is the only thing deciding — they get their own tests below.
    monkeypatch.setenv("LEADER_PRECEDENT_FREE_CEILING", "5")
    _seed_experience()

    body = client.post(
        "/api/chat", json={"message": "create a workspace named fast", "auto_approve": True}
    ).json()
    assert body["pending_plan"] is None
    assert body["executed"] is True
    assert (isolated_workspace_root / "fast").is_dir()


def test_ac5_trust_mode_does_not_bypass_novel_high_risk_work(
    client, offline_agent, isolated_workspace_root, monkeypatch
):
    # spec 011 FR-18 / scenario 4 (supersedes 009 FR-7's unconditional bypass): standing consent is
    # consent, not carte blanche. An operation above the precedent-free ceiling with no matching
    # precedent still asks, and still creates nothing.
    _seed_experience()
    body = client.post(
        "/api/chat", json={"message": "create a workspace named novel", "auto_approve": True}
    ).json()
    assert body["pending_plan"] is not None
    assert body["executed"] is False
    assert not (isolated_workspace_root / "novel").exists()


def test_ac5_cold_start_asks_even_in_trust_mode(client, offline_agent, isolated_workspace_root, monkeypatch):
    # spec 011 FR-20 / AC-9: with nothing recorded, nothing is delegable — the scope of standing
    # consent is what experience defines, and a fresh install has defined none.
    monkeypatch.setenv("LEADER_PRECEDENT_FREE_CEILING", "5")
    body = client.post(
        "/api/chat", json={"message": "create a workspace named coldstart", "auto_approve": True}
    ).json()
    assert body["pending_plan"] is not None
    assert body["executed"] is False
    assert not (isolated_workspace_root / "coldstart").exists()


def test_ac6_settings_are_readable_and_updatable_over_rest(client):
    # AC-6 / FR-8: parity with the model endpoints (P9).
    assert client.get("/api/settings").json()["auto_approve"] is False
    updated = client.post("/api/settings", json={"auto_approve": True}).json()
    assert updated["auto_approve"] is True
    assert updated["agent_model"]
    assert client.get("/api/settings").json()["auto_approve"] is True


def test_ac6_persisted_trust_mode_survives_restart_and_applies(
    client, offline_agent, isolated_workspace_root, monkeypatch
):
    # AC-6 / FR-8: the setting lives in the runtime settings file, so a fresh process picks it
    # up and requests without an override are auto-approved.
    monkeypatch.setenv("LEADER_PRECEDENT_FREE_CEILING", "5")
    _seed_experience()
    client.post("/api/settings", json={"auto_approve": True})

    from fastapi.testclient import TestClient

    from app.api import app as fresh_app

    # The setting is only ever read from the settings file, so a fresh client reads what a
    # restarted process would.
    restarted = TestClient(fresh_app)
    assert restarted.get("/api/settings").json()["auto_approve"] is True

    body = restarted.post("/api/chat", json={"message": "create a workspace named trusted"}).json()
    assert body["pending_plan"] is None
    assert body["executed"] is True
    assert (isolated_workspace_root / "trusted").is_dir()


def test_ac7_per_request_override_wins_both_ways(
    client, offline_agent, isolated_workspace_root, monkeypatch
):
    # AC-7 / FR-9: explicit false forces a prompt with trust on; explicit true grants with
    # trust off. Precedence is per-turn only.
    monkeypatch.setenv("LEADER_PRECEDENT_FREE_CEILING", "5")
    _seed_experience()
    client.post("/api/settings", json={"auto_approve": True})
    gated = client.post(
        "/api/chat", json={"message": "create a workspace named forced", "auto_approve": False}
    ).json()
    assert gated["pending_plan"] is not None
    assert not (isolated_workspace_root / "forced").exists()

    client.post("/api/settings", json={"auto_approve": False})
    ran = client.post(
        "/api/chat", json={"message": "create a workspace named waved", "auto_approve": True}
    ).json()
    assert ran["executed"] is True
    assert (isolated_workspace_root / "waved").is_dir()


def test_ac7_omitted_auto_approve_uses_the_persisted_default(client, offline_agent, monkeypatch):
    # AC-7 / FR-9: absent the per-request value, the stored setting decides.
    monkeypatch.setenv("LEADER_PRECEDENT_FREE_CEILING", "5")
    _seed_experience()
    off = client.post("/api/chat", json={"message": "create a workspace named prompted"}).json()
    assert off["pending_plan"] is not None

    client.post("/api/settings", json={"auto_approve": True})
    on = client.post("/api/chat", json={"message": "create a workspace named silent"}).json()
    assert on["executed"] is True


def test_ac5_auto_approved_action_stays_auditable(
    client, offline_agent, isolated_workspace_root, monkeypatch
):
    # AC-5 / FR-6: trust mode grants approval, it does not disable the audit trail.
    monkeypatch.setenv("LEADER_PRECEDENT_FREE_CEILING", "5")
    _seed_experience()
    client.post("/api/chat", json={"message": "create a workspace named audited", "auto_approve": True})
    workspace = isolated_workspace_root / "audited"
    assert (workspace / "vault" / "wiki" / "log.md").is_file()
    assert _git(workspace, "log", "--oneline").strip()


# --- AC-8: the UI control -------------------------------------------------


def test_ac8_ui_exposes_the_toggle_over_api_only():
    # AC-8 / FR-10 / P9: the toggle exists in the settings quick menu and the UI reaches the
    # setting only over /api/settings — never by importing the capability layer.
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "app" / "ui.py").read_text(encoding="utf-8")
    assert "Auto-approve" in src
    assert "/api/settings" in src
    assert "from .capabilities" not in src and "import capabilities" not in src


def test_ac8_ui_reflects_the_persisted_state(client, ui_over_api):
    # AC-8 / FR-10: the control loads its value from the persisted setting.
    client.post("/api/settings", json={"auto_approve": True})
    _checkbox, hint, state = ui_over_api._trust_initial()
    assert state is True
    assert "on" in str(hint).lower()


def test_ac8_ui_toggle_persists_through_the_api(client, ui_over_api):
    # AC-8 / FR-10: flipping the control writes through /api/settings.
    ui_over_api._pick_trust(True)
    assert client.get("/api/settings").json()["auto_approve"] is True
    ui_over_api._pick_trust(False)
    assert client.get("/api/settings").json()["auto_approve"] is False


# --- AC-9: the agent cannot self-approve or self-trust --------------------


def test_ac9_agent_has_no_settings_or_chat_tools():
    # AC-9 / FR-11: no tool lets the agent read or set trust mode, or re-enter chat.
    from app import agent, models

    names = {s.name for s in agent._capability_tool_specs(None, [], None, None)}
    assert {"get_settings", "update_settings", "chat", "ask"}.isdisjoint(names)
    assert "auto_approve" not in {
        f for s in agent._capability_tool_specs(None, [], None, None) for f in s.schema
    }
    assert "auto_approve" in models.ChatRequest.model_fields  # operator-facing only


def test_ac9_agent_cannot_raise_an_approval_card(client):
    # AC-9 / FR-12: request_interaction refuses kind='approval'; approval is capability-layer
    # only. Clarification and notification remain available (spec 008 FR-18).
    import asyncio

    from app import agent, capabilities

    capabilities.create_workspace("demo")
    cid = "conv-ac9"
    raised: list = []
    specs = {s.name: s for s in agent._capability_tool_specs("demo", [], cid, raised)}
    call = specs["request_interaction"].handler

    denied = asyncio.run(call({"kind": "approval", "prompt": "let me do it", "options": "[]"}))
    assert "error" in denied["content"][0]["text"]
    assert raised == []

    ok = asyncio.run(
        call({"kind": "clarification", "prompt": "which one?", "options": '["A","B"]'})
    )
    assert "error" not in ok["content"][0]["text"]
    assert [i.kind for i in raised] == ["clarification"]
    assert all(i.kind != "approval" for i in raised)

    # And the approval card that does exist comes from the capability layer's plan path.
    p = capabilities.plan(
        __import__("app.models", fromlist=["models"]).PlanRequest(
            workspace="demo", request="create a workspace named gated"
        )
    )
    assert p.requires_approval is True


# --- AC-10: the keyword regex is gone ------------------------------------


def test_ac10_consequential_regex_is_removed():
    # AC-10 / FR-2 / P12: risk comes from the data-declared tiers, not a message regex.
    from pathlib import Path

    from app import capabilities

    assert not hasattr(capabilities, "_CONSEQUENTIAL")
    src = (Path(__file__).resolve().parents[1] / "app" / "capabilities.py").read_text(encoding="utf-8")
    assert "_CONSEQUENTIAL" not in src
    assert "EFFECTS" in src
