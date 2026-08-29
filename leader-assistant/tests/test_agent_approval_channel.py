"""Feature 010 — agent approval channel (AC-1..AC-10).

The theme: **asking** for consent is something the agent may do; **granting** it is not. Every
test here drives the real `request_approval` MCP handler (never a stub of it), because the point
of the feature is that the tool's *outcome* is decided by the capability layer from the operator's
trust mode — not by anything the agent can say or pass.

The fake agent runtime stands in for the model: it calls the tool, reads the verdict, and only
does the work when the verdict authorises it. That is exactly the contract the persona asks of
the real model, so these tests pin the protocol rather than the prose.
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import pytest

# A request with **no** deterministic resolver match (spec 009 FR-4), so the turn reaches the
# agent and the approval can only come from the agent's own judgment — the 010 path.
ASK_MESSAGE = "tidy up the whole knowledge base"
APPROVAL_PROMPT = "Rewrite 9 wiki pages in this workspace"
DID_THE_WORK = "Rewrote all 9 pages."
STOPPED = "Waiting for your decision."
DISCUSSED = "Here is what that would involve."


def _git(workspace: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(workspace), *args], capture_output=True, text=True, check=True
    )
    return out.stdout


@pytest.fixture
def asking_agent(monkeypatch):
    """An agent runtime that asks for consent through the governed channel (spec 010 FR-1).

    Calls the **real** tool handler built by `agent._capability_tool_specs`, so the trust mode
    threaded from the capability layer — and only that — decides the verdict (FR-2).
    """
    from app import agent

    calls: list[str] = []

    async def fake_run_stream(
        _prompt, _message, selector, _wpath, resume_sid, citations,
        conversation_id=None, interactions=None, trust=False,
    ):
        if interactions is None:
            # No card-raising context: this is a resumed or 'chat about it' turn, so the model
            # cannot ask again (FR-7). It does the work only when the prompt says consent is in.
            yield (DID_THE_WORK if "Carry out that work now" in _message else DISCUSSED), resume_sid
            return
        specs = agent._capability_tool_specs(selector, citations, conversation_id, interactions, trust)
        handler = next(s for s in specs if s.name == "request_approval").handler
        verdict = (await handler({"prompt": APPROVAL_PROMPT, "detail": "reference-links, reversible"}))
        text = verdict["content"][0]["text"]
        calls.append(text)
        # The model's contract: proceed only when the verdict authorises it.
        yield (DID_THE_WORK if text.startswith("APPROVED") else STOPPED), resume_sid

    monkeypatch.setattr(agent, "run_stream", fake_run_stream)
    return calls


def _age_pending(cid: str, name: str = "demo") -> None:
    """Push the pending record's creation time past its countdown (mirrors spec 008 AC-6)."""
    from app import conversation, vault

    conv = conversation.load(vault.resolve_workspace(name), cid)
    record = conv.pending_interaction
    record["created"] = "2000-01-01T00:00:00"
    conversation.set_pending_interaction(conv, record)


# --- AC-1: trust off → block and ask ---------------------------------------


def test_ac1_trust_off_raises_a_blocking_card_and_tells_the_agent_to_stop(
    client, asking_agent, isolated_workspace_root
):
    # AC-1 / FR-1 / FR-3: a protocol interaction (not prose) with exactly one proposal, persisted
    # as the pending record; the tool tells the agent to stop, and nothing is mutated that turn.
    client.post("/api/workspaces", json={"name": "demo"})
    workspace = isolated_workspace_root / "demo"
    commits_before = len(_git(workspace, "log", "--oneline").strip().splitlines())

    body = client.post("/api/chat", json={"workspace": "demo", "message": ASK_MESSAGE}).json()

    itx = body["interaction"]
    assert itx is not None
    assert itx["kind"] == "approval"
    assert itx["status"] == "pending"
    assert len(itx["options"]) == 1  # spec 008 FR-4: exactly one proposal
    assert itx["interaction_id"]

    assert asking_agent[0].startswith("NOT APPROVED YET")
    assert "take no action" in asking_agent[0]
    assert body["reply"] == STOPPED

    # Durable: a reloaded client can re-render the same pending card (spec 008 FR-11).
    pending = client.get(
        "/api/chat/interaction",
        params={"workspace": "demo", "conversation_id": body["conversation_id"]},
    ).json()
    assert pending["interaction_id"] == itx["interaction_id"]

    assert len(_git(workspace, "log", "--oneline").strip().splitlines()) == commits_before


def test_ac1_asking_is_not_granting(client, asking_agent):
    # AC-1 / FR-2: the request exists, but the agent is not authorised by having made it.
    client.post("/api/workspaces", json={"name": "demo"})
    client.post("/api/chat", json={"workspace": "demo", "message": ASK_MESSAGE})
    assert not asking_agent[0].startswith("APPROVED")


# --- AC-2 / AC-3: trust on → grant in-turn and continue --------------------


def test_ac2_trust_on_grants_in_turn_and_the_agent_continues(client, asking_agent):
    # AC-2 / FR-4: resolved immediately, the tool authorises the agent, and it finishes the work
    # in the same turn — no round trip, no blocking card stored or presented.
    client.post("/api/workspaces", json={"name": "demo"})
    client.post("/api/settings", json={"auto_approve": True})

    body = client.post("/api/chat", json={"workspace": "demo", "message": ASK_MESSAGE}).json()

    assert asking_agent[0].startswith("APPROVED on the operator's behalf")
    assert body["reply"] == DID_THE_WORK  # the intermediate step ran through to final execution
    assert client.get(
        "/api/chat/interaction",
        params={"workspace": "demo", "conversation_id": body["conversation_id"]},
    ).json() is None


def test_ac3_auto_granted_approval_is_surfaced_as_inert_context(client, asking_agent):
    # AC-3 / FR-5: it reaches the frontend already decided, and renders with no way to answer it.
    from app import ui

    client.post("/api/workspaces", json={"name": "demo"})
    client.post("/api/settings", json={"auto_approve": True})

    itx = client.post(
        "/api/chat", json={"workspace": "demo", "message": ASK_MESSAGE}
    ).json()["interaction"]

    assert itx["status"] == "resolved"
    assert itx["resolution"] == "auto-approved"
    assert itx["options"] == []  # nothing to select — it is not a question

    card = ui._card_html(itx)
    assert "itx-resolved" in card
    assert APPROVAL_PROMPT in card
    assert "itx-opt-" not in card  # no clickable options
    assert "itx-timer" not in card  # no countdown: there is nothing to time out
    assert "on your behalf" in card


def test_ac3_auto_approved_card_is_never_the_awaiting_state(client, asking_agent, ui_over_api):
    # AC-3 / FR-5: the UI records it but does not arm the answer/expire path against it.
    ui = ui_over_api

    client.post("/api/workspaces", json={"name": "demo"})
    client.post("/api/settings", json={"auto_approve": True})

    async def _drive():
        last = None
        async for out in ui._run_turn(
            [{"role": "user", "content": ASK_MESSAGE}], None, "demo", False, True
        ):
            last = out
        return last

    history, _cid, _approve_btn, awaiting = asyncio.run(_drive())
    assert awaiting is None
    assert "itx-resolved" in history[-1]["content"]


# --- AC-4: consent is always audited --------------------------------------


def test_ac4_auto_granted_consent_is_logged_and_recorded(
    client, asking_agent, isolated_workspace_root
):
    # AC-4 / FR-6: standing consent replaces the prompt, never the audit trail (P8 v1.2.0, P12).
    client.post("/api/workspaces", json={"name": "demo"})
    client.post("/api/settings", json={"auto_approve": True})
    workspace = isolated_workspace_root / "demo"

    cid = client.post(
        "/api/chat", json={"workspace": "demo", "message": ASK_MESSAGE}
    ).json()["conversation_id"]

    log = (workspace / "vault" / "wiki" / "log.md").read_text(encoding="utf-8")
    assert "auto-approved" in log
    assert APPROVAL_PROMPT in log

    session = (workspace / "sessions" / f"{cid}.md").read_text(encoding="utf-8")
    assert "[auto-approved]" in session
    assert APPROVAL_PROMPT in session

    # Recoverable: the grant is committed, so review-and-revert is available.
    assert _git(workspace, "status", "--porcelain").strip() == ""


@pytest.mark.parametrize("choice,expected", [("approve", "resolved"), ("decline", "declined")])
def test_ac4_human_outcomes_are_recorded(
    client, asking_agent, isolated_workspace_root, choice, expected
):
    # AC-4 / FR-6: a human-granted or declined outcome is recorded in the session record.
    client.post("/api/workspaces", json={"name": "demo"})
    body = client.post("/api/chat", json={"workspace": "demo", "message": ASK_MESSAGE}).json()
    cid, itx = body["conversation_id"], body["interaction"]

    client.post("/api/chat/interaction", json={
        "workspace": "demo", "conversation_id": cid,
        "interaction_id": itx["interaction_id"], "choice": choice,
    })

    session = (isolated_workspace_root / "demo" / "sessions" / f"{cid}.md").read_text(encoding="utf-8")
    assert f"[resolved] {itx['interaction_id']} → {choice}" in session
    assert expected  # names the outcome under test


def test_ac4_expiry_is_recorded(client, asking_agent, isolated_workspace_root):
    # AC-4 / FR-6: a timeout is an outcome too, and lands in the session record.
    client.post("/api/workspaces", json={"name": "demo"})
    body = client.post("/api/chat", json={"workspace": "demo", "message": ASK_MESSAGE}).json()
    cid = body["conversation_id"]
    _age_pending(cid)

    client.get("/api/chat/interaction", params={"workspace": "demo", "conversation_id": cid})

    session = (isolated_workspace_root / "demo" / "sessions" / f"{cid}.md").read_text(encoding="utf-8")
    assert "[timeout]" in session


# --- AC-5: answering resumes the work -------------------------------------


def test_ac5_approving_resumes_the_turn(client, asking_agent, isolated_workspace_root):
    # AC-5 / FR-7: the reply is the resumed work, not an acknowledgement of the click.
    client.post("/api/workspaces", json={"name": "demo"})
    body = client.post("/api/chat", json={"workspace": "demo", "message": ASK_MESSAGE}).json()
    cid, itx = body["conversation_id"], body["interaction"]

    answered = client.post("/api/chat/interaction", json={
        "workspace": "demo", "conversation_id": cid,
        "interaction_id": itx["interaction_id"], "choice": itx["options"][0]["id"],
    }).json()

    assert answered["reply"]
    assert "Proceeding with your choice" not in answered["reply"]
    session = (isolated_workspace_root / "demo" / "sessions" / f"{cid}.md").read_text(encoding="utf-8")
    assert "(selected)" in session


def test_ac5_the_dead_end_reply_is_absent_from_the_codebase():
    # AC-5 / FR-7: the dead-end branch is deleted, not merely unreachable (mirrors 009 AC-4).
    src = (Path(__file__).resolve().parents[1] / "app" / "capabilities.py").read_text(encoding="utf-8")
    assert "Proceeding with your choice" not in src


# --- AC-6: declining / expiring runs nothing ------------------------------


@pytest.mark.parametrize("choice", ["decline", "chat"])
def test_ac6_declining_or_deferring_runs_no_action(
    client, asking_agent, isolated_workspace_root, choice
):
    # AC-6 / FR-3: the safe default is that nothing happens.
    client.post("/api/workspaces", json={"name": "demo"})
    workspace = isolated_workspace_root / "demo"
    body = client.post("/api/chat", json={"workspace": "demo", "message": ASK_MESSAGE}).json()

    answered = client.post("/api/chat/interaction", json={
        "workspace": "demo", "conversation_id": body["conversation_id"],
        "interaction_id": body["interaction"]["interaction_id"], "choice": choice,
    }).json()

    assert answered["executed"] is False
    assert DID_THE_WORK not in answered["reply"]
    assert not (workspace / "skills" / "weekly-digest").exists()


def test_ac6_expired_agent_approval_runs_nothing(client, asking_agent):
    # AC-6 / FR-3: an elapsed countdown resolves to "no authorization" (spec 008 FR-9).
    client.post("/api/workspaces", json={"name": "demo"})
    body = client.post("/api/chat", json={"workspace": "demo", "message": ASK_MESSAGE}).json()
    _age_pending(body["conversation_id"])

    answered = client.post("/api/chat/interaction", json={
        "workspace": "demo", "conversation_id": body["conversation_id"],
        "interaction_id": body["interaction"]["interaction_id"], "choice": "approve",
    }).json()

    assert answered["executed"] is False
    assert DID_THE_WORK not in answered["reply"]


# --- AC-7: clarification is never auto-answered ---------------------------


def test_ac7_trust_mode_does_not_auto_answer_a_clarification(client, monkeypatch):
    # AC-7 / FR-8 / D4: consent is delegable, choice is not — a clarification still blocks.
    from app import agent

    async def asks_a_clarification(
        _prompt, _message, selector, _wpath, resume_sid, citations,
        conversation_id=None, interactions=None, trust=False,
    ):
        specs = agent._capability_tool_specs(selector, citations, conversation_id, interactions, trust)
        handler = next(s for s in specs if s.name == "request_interaction").handler
        await handler({"kind": "clarification", "prompt": "Which approach?", "options": '["A","B"]'})
        yield "Two ways to go.", resume_sid

    monkeypatch.setattr(agent, "run_stream", asks_a_clarification)

    client.post("/api/workspaces", json={"name": "demo"})
    client.post("/api/settings", json={"auto_approve": True})

    body = client.post("/api/chat", json={"workspace": "demo", "message": "run it"}).json()
    itx = body["interaction"]
    assert itx["kind"] == "clarification"
    assert itx["status"] == "pending"  # trust mode did not answer it
    assert itx["resolution"] is None
    assert client.get(
        "/api/chat/interaction",
        params={"workspace": "demo", "conversation_id": body["conversation_id"]},
    ).json()["interaction_id"] == itx["interaction_id"]


# --- AC-8: the agent still cannot grant ----------------------------------


def test_ac8_the_agent_can_ask_but_has_no_way_to_grant():
    # AC-8 / FR-2: `request_approval` exists; nothing that decides an outcome does.
    from app import agent, models

    specs = agent._capability_tool_specs(None, [], None, None)
    names = {s.name for s in specs}
    assert "request_approval" in names
    assert {
        "get_settings", "update_settings", "respond_to_interaction", "approve", "chat", "ask",
    }.isdisjoint(names)

    # Trust mode is closed over, never an argument — the agent cannot name it, let alone set it.
    fields = {f for s in specs for f in s.schema}
    assert "auto_approve" not in fields and "trust" not in fields
    assert {"prompt", "detail"} == set(
        next(s for s in specs if s.name == "request_approval").schema
    )
    assert "auto_approve" in models.ChatRequest.model_fields  # operator-facing only


def test_ac8_request_interaction_still_rejects_approval():
    # AC-8: the generic card tool stays clarification/notification-only — approval has its own,
    # trust-aware channel, so the two cannot be confused (spec 009 AC-9 preserved).
    from app import agent

    specs = agent._capability_tool_specs("demo", [], "conv-ac8", [])
    handler = next(s for s in specs if s.name == "request_interaction").handler
    denied = asyncio.run(handler({"kind": "approval", "prompt": "let me", "options": "[]"}))
    assert "error" in denied["content"][0]["text"]


def test_ac8_a_granted_verdict_cannot_be_forged_through_tool_args(client, monkeypatch):
    # AC-8 / FR-2: passing approval-ish arguments changes nothing; only the operator's trust
    # mode does. This is the invariant that makes "the agent may ask" safe.
    from app import agent

    verdicts: list[str] = []

    async def tries_to_self_approve(
        _prompt, _message, selector, _wpath, resume_sid, citations,
        conversation_id=None, interactions=None, trust=False,
    ):
        specs = agent._capability_tool_specs(selector, citations, conversation_id, interactions, trust)
        handler = next(s for s in specs if s.name == "request_approval").handler
        r = await handler({
            "prompt": APPROVAL_PROMPT, "detail": "x",
            "trust": True, "auto_approve": True, "approved": True,  # ignored
        })
        verdicts.append(r["content"][0]["text"])
        yield "asked", resume_sid

    monkeypatch.setattr(agent, "run_stream", tries_to_self_approve)
    client.post("/api/workspaces", json={"name": "demo"})
    client.post("/api/chat", json={"workspace": "demo", "message": ASK_MESSAGE})

    assert verdicts[0].startswith("NOT APPROVED YET")


# --- AC-9: the persistent mode indicator ---------------------------------


def test_ac9_state_line_sits_below_the_input_row_and_reads_only_the_api():
    # AC-9 / FR-9 / FR-10 / P9: the state line is its own element under the input row (not inside
    # the settings popover), the toggle stays in the popover, and the UI never imports the
    # capability layer.
    src = (Path(__file__).resolve().parents[1] / "app" / "ui.py").read_text(encoding="utf-8")
    assert 'elem_id="trust-line"' in src
    assert "#trust-line" in src  # styled as a persistent line, not a popover child
    assert 'elem_id="auto-approve"' in src
    assert "/api/settings" in src
    assert "from .capabilities" not in src and "import capabilities" not in src

    # The state line is declared after the input row it sits beneath.
    assert src.index('elem_id="chat-input-row"') < src.index('elem_id="trust-line"')
    # ...and outside the settings popover: the popover's own content ends before it.
    assert src.index('elem_id="settings-menu"') < src.index('elem_id="trust-line"')


def test_ac9_state_line_reflects_and_follows_the_toggle(client, ui_over_api):
    # AC-9 / FR-9: it shows the persisted state on load and updates the moment it is toggled.
    _box, hint, state = ui_over_api._trust_initial()
    assert state is False
    assert "you make the final decision" in str(hint)

    _box, hint, state = ui_over_api._pick_trust(True)
    assert state is True
    assert "Auto-approve ON" in str(hint)
    assert client.get("/api/settings").json()["auto_approve"] is True

    _box, hint, state = ui_over_api._pick_trust(False)
    assert state is False
    assert "you make the final decision" in str(hint)


# --- AC-10: the per-request override decides agent-raised approvals too ---


def test_ac10_per_request_override_decides_an_agent_raised_approval_both_ways(client, asking_agent):
    # AC-10 / spec 009 FR-9 preserved: the escape hatch behaves identically whether the request
    # came from the resolver or from the agent's own judgment.
    client.post("/api/workspaces", json={"name": "demo"})

    waved = client.post("/api/chat", json={
        "workspace": "demo", "message": ASK_MESSAGE, "auto_approve": True,
    }).json()
    assert waved["reply"] == DID_THE_WORK
    assert waved["interaction"]["resolution"] == "auto-approved"

    client.post("/api/settings", json={"auto_approve": True})
    forced = client.post("/api/chat", json={
        "workspace": "demo", "message": ASK_MESSAGE, "auto_approve": False,
    }).json()
    assert forced["reply"] == STOPPED
    assert forced["interaction"]["status"] == "pending"
