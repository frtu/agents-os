"""Tests for the agent<->user interaction channel (feature 008 user stories).

Each test maps to an acceptance criterion in
``specs/008-agent-user-interaction/spec.md``. The protocol is exercised over the
REST surface (parity, P9) and, where a request must be *created* by the backend
mid-task, directly through the capability layer. The ``offline_agent`` fixture
forces the deterministic no-LLM path so "chat about it" and routine turns are
reproducible.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app import capabilities
from app.capabilities import INTERACTION_TIMEOUT_MSG
from app.vault import WorkspaceError


def sse_events(text: str) -> list[dict]:
    return [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]


def _session_files(selector: str | None):
    _name, wpath = capabilities.resolve_for_chat(selector)
    sessions = wpath / "sessions"
    return sorted(sessions.glob("*.md")) if sessions.is_dir() else []


def _consequential_chat(client, message, conversation_id=None):
    body = {"message": message}
    if conversation_id:
        body["conversation_id"] = conversation_id
    return client.post("/api/chat", json=body).json()


# --- AC-1 / AC-13: plan-first approval streamed as an interaction --------------


def test_ac1_ac13_consequential_turn_streams_approval_interaction(client, isolated_workspace_root):
    # AC-1 (FR-1/FR-2) + AC-13 (FR-17): a consequential turn ends with an approval interaction that
    # wraps the plan; the stream carries it before the turn's final event closes.
    streamed = client.post("/api/chat/stream", json={"message": "create a workspace named ac1ws"})
    assert streamed.status_code == 200
    last = sse_events(streamed.text)[-1]
    assert last["done"] is True
    assert last["pending_plan"] is not None          # plan shown (FR-5)
    assert last["interaction"] is not None            # delivered as an interaction (FR-17)
    assert last["interaction"]["kind"] == "approval"
    # The affirmative proposal plus spec 011 FR-38's optional "approve all similar" batch option.
    assert [o["id"] for o in last["interaction"]["options"]] == ["approve", "approve_all"]
    assert last["executed"] is False                  # nothing runs without explicit approval (P8)


# --- AC-2: approval yes/no, neither inferred ----------------------------------


def test_ac2_approval_yes_proceeds(client, isolated_workspace_root):
    # AC-2 (FR-4/FR-14): selecting the proposal executes; nothing ran until the explicit click.
    first = _consequential_chat(client, "create a workspace named ac2yes")
    cid, itx = first["conversation_id"], first["interaction"]
    assert not (isolated_workspace_root / "ac2yes").exists()  # not yet
    r = client.post("/api/chat/interaction", json={
        "conversation_id": cid, "interaction_id": itx["interaction_id"], "choice": "approve",
    }).json()
    assert r["executed"] is True
    assert (isolated_workspace_root / "ac2yes" / "vault" / "wiki").is_dir()


def test_ac2_approval_no_does_not_proceed(client, isolated_workspace_root):
    # AC-2 (FR-14): declining performs no consequential action.
    first = _consequential_chat(client, "create a workspace named ac2no")
    cid, itx = first["conversation_id"], first["interaction"]
    r = client.post("/api/chat/interaction", json={
        "conversation_id": cid, "interaction_id": itx["interaction_id"], "choice": "decline",
    }).json()
    assert r["executed"] is False
    assert not (isolated_workspace_root / "ac2no").exists()


# --- AC-3: clarification bounds + selection continues -------------------------


def test_ac3_clarification_selection_continues_and_bounds_enforced(
    client, offline_agent, isolated_workspace_root
):
    # AC-3 (FR-5/FR-6): a 2–4-option clarification is valid and one selection continues; 0/1/>4 and a
    # wrong approval count are rejected as malformed and never rendered. Selecting **resumes the
    # turn** rather than acknowledging the choice (spec 010 FR-7 / AC-5).
    capabilities.create_workspace("demo")
    itx = capabilities.create_interaction(
        "demo", None, "clarification", "Pick an approach",
        ["Refactor now", "Ship then refactor"],
    )
    assert len(itx.options) == 2
    r = client.post("/api/chat/interaction", json={
        "workspace": "demo", "conversation_id": itx.conversation_id,
        "interaction_id": itx.interaction_id, "choice": itx.options[0].id,
    }).json()
    assert r["reply"]
    assert "Proceeding with your choice" not in r["reply"]  # the dead-end is gone (spec 010 FR-7)
    # The selection is recorded in the durable session record and nothing stays pending.
    detail = client.get(
        "/api/sessions/" + itx.conversation_id, params={"workspace": "demo"}
    ).json()
    assert any("Refactor now" in m["text"] for m in detail["messages"] if m["role"] == "user")
    assert client.get(
        "/api/chat/interaction",
        params={"workspace": "demo", "conversation_id": itx.conversation_id},
    ).json() is None

    with pytest.raises(WorkspaceError):  # clarification needs 2..4
        capabilities.create_interaction("demo", None, "clarification", "one?", ["only"])
    with pytest.raises(WorkspaceError):  # >4
        capabilities.create_interaction("demo", None, "clarification", "too many", list("ABCDE"))
    with pytest.raises(WorkspaceError):  # approval needs exactly 1
        capabilities.create_interaction("demo", None, "approval", "zero?", [])


# --- AC-4: "chat about it" scopes discussion, re-presents a new id -------------


def test_ac4_chat_about_it_does_not_resolve_and_represents_new_id(client, offline_agent, isolated_workspace_root):
    # AC-4 (FR-7/D9): "chat about it" discusses without resolving and re-presents a NEW id that
    # supersedes the old; afterward the fresh id still approves and executes.
    first = _consequential_chat(client, "create a workspace named ac4ws")
    cid, old_id = first["conversation_id"], first["interaction"]["interaction_id"]

    chatted = client.post("/api/chat/interaction", json={
        "conversation_id": cid, "interaction_id": old_id, "choice": "chat",
    }).json()
    fresh = chatted["interaction"]
    assert fresh is not None and fresh["interaction_id"] != old_id  # superseded (D9)
    assert not (isolated_workspace_root / "ac4ws").exists()          # not resolved by chatting

    # The superseded id is no longer answerable (FR-16).
    stale = client.post("/api/chat/interaction", json={
        "conversation_id": cid, "interaction_id": old_id, "choice": "approve",
    }).json()
    assert "no longer awaiting" in stale["reply"]
    assert not (isolated_workspace_root / "ac4ws").exists()

    # The fresh interaction still authorizes execution.
    done = client.post("/api/chat/interaction", json={
        "conversation_id": cid, "interaction_id": fresh["interaction_id"], "choice": "approve",
    }).json()
    assert done["executed"] is True
    assert (isolated_workspace_root / "ac4ws" / "vault" / "wiki").is_dir()


# --- AC-5: bottom chat box starts a new task, never answers the card -----------


def test_ac5_new_task_does_not_answer_pending_interaction(client, offline_agent, isolated_workspace_root):
    # AC-5 (FR-8): a message in the same conversation is a new top-level turn; the pending
    # interaction stays pending and answerable, and nothing consequential runs.
    first = _consequential_chat(client, "create a workspace named ac5ws")
    cid, itx_id = first["conversation_id"], first["interaction"]["interaction_id"]

    second = _consequential_chat(client, "what is this project about?", conversation_id=cid)
    assert second["executed"] is False

    pending = client.get("/api/chat/interaction", params={"conversation_id": cid}).json()
    assert pending is not None and pending["interaction_id"] == itx_id
    assert not (isolated_workspace_root / "ac5ws").exists()


# --- AC-6: timeout default/configurable + expiry aborts with fixed message -----


def test_ac6_approval_default_is_two_minutes(client, isolated_workspace_root):
    # AC-6 (FR-9/D5): an approval makes the operator read the maker/checker blast radius before
    # consenting, so it now defaults to 120s (same "read then decide" cost as a clarification).
    first = _consequential_chat(client, "create a workspace named ac6def")
    assert first["interaction"]["timeout_seconds"] == 120


def test_ac6_decision_kinds_are_two_minutes_notification_stays_30s(isolated_workspace_root):
    # AC-6 (FR-9/D5): anything the user must *decide* (approval, clarification) defaults to 120s; only
    # a notification, which just needs dismissing, keeps 30s.
    capabilities.create_workspace("ac6kind")
    # Separate conversations: only one blocking card may be pending per conversation (FR-15).
    clarify = capabilities.create_interaction("ac6kind", None, "clarification", "which?", ["A", "B"])
    assert clarify.timeout_seconds == 120
    approve = capabilities.create_interaction("ac6kind", None, "approval", "ok?", ["yes"])
    assert approve.timeout_seconds == 120
    note = capabilities.create_interaction("ac6kind", clarify.conversation_id, "notification", "fyi")
    assert note.timeout_seconds == 30


def test_ac6_timeout_configurable(client, isolated_workspace_root, monkeypatch):
    # AC-6 (FR-9/D5): the system-wide default is configurable.
    monkeypatch.setenv("LEADER_INTERACTION_TIMEOUT", "5")
    first = _consequential_chat(client, "create a workspace named ac6cfg")
    assert first["interaction"]["timeout_seconds"] == 5


def test_ac6_configured_timeout_overrides_the_clarification_default(
    isolated_workspace_root, monkeypatch
):
    # AC-6 (FR-9/D5): an explicit operator instruction outranks the per-kind default.
    monkeypatch.setenv("LEADER_INTERACTION_TIMEOUT", "7")
    capabilities.create_workspace("ac6ovr")
    clarify = capabilities.create_interaction("ac6ovr", None, "clarification", "which?", ["A", "B"])
    assert clarify.timeout_seconds == 7


def test_ac6_expiry_aborts_with_fixed_message_no_action(client, isolated_workspace_root):
    # AC-6 (FR-9/FR-14/D6): once the countdown elapses, responding aborts with the exact message
    # and runs nothing consequential.
    from app import conversation, vault

    first = _consequential_chat(client, "create a workspace named ac6exp")
    cid, itx_id = first["conversation_id"], first["interaction"]["interaction_id"]

    conv = conversation.load(vault.resolve_workspace(None), cid)
    rec = conv.pending_interaction
    rec["created"] = "2000-01-01T00:00:00"  # age it well past the timeout
    conversation.set_pending_interaction(conv, rec)

    r = client.post("/api/chat/interaction", json={
        "conversation_id": cid, "interaction_id": itx_id, "choice": "approve",
    }).json()
    assert r["reply"] == INTERACTION_TIMEOUT_MSG
    assert r["executed"] is False
    assert not (isolated_workspace_root / "ac6exp").exists()


# --- FR-16: an answer/approve resolves in its OWN conversation, never forks a new one ---


def test_fr16_answer_with_blank_conversation_id_is_rejected_without_forking(isolated_workspace_root):
    # spec 008 FR-16 (regression): a card answered while the prior turn was still streaming used to
    # arrive with a blank conversation id and silently mint a NEW conversation, orphaning the live
    # card (it could then only time out). A blank id must now be rejected with no new record.
    capabilities.create_workspace("fr16ans")
    assert _session_files("fr16ans") == []
    ans = asyncio.run(capabilities.respond_to_interaction("fr16ans", "", "itx-nope", "approve"))
    assert "no longer awaiting" in ans.reply.lower()
    assert _session_files("fr16ans") == []  # no phantom conversation minted


def test_fr16_approve_with_blank_conversation_id_does_not_fork(isolated_workspace_root):
    # spec 008 FR-16: approving targets an existing pending plan; a blank id must not fork a thread.
    capabilities.create_workspace("fr16app")
    assert _session_files("fr16app") == []
    ans = asyncio.run(capabilities.ask("fr16app", "(approve)", "", approve=True))
    assert "no pending plan" in ans.reply.lower()
    assert _session_files("fr16app") == []  # nothing materialized


def test_fr16_answer_with_correct_id_resolves_in_place(isolated_workspace_root):
    # spec 008 FR-16: the happy path — answering with the card's own id resolves within the same
    # conversation record; no second file appears.
    capabilities.create_workspace("fr16ok")
    itx = capabilities.create_interaction("fr16ok", None, "approval", "ok?", ["yes"])
    before = _session_files("fr16ok")
    assert len(before) == 1  # the blocking card materialized exactly one record
    ans = asyncio.run(
        capabilities.respond_to_interaction("fr16ok", itx.conversation_id, itx.interaction_id, "decline")
    )
    assert ans.conversation_id == itx.conversation_id
    assert _session_files("fr16ok") == before  # answered in place — no new thread


def test_fr16_rest_answer_with_blank_conversation_id_is_rejected(client, isolated_workspace_root):
    # Parity (P9): the same guard holds over REST — a blank conversation id is rejected, not forked.
    capabilities.create_workspace("fr16rest")
    r = client.post("/api/chat/interaction", json={
        "workspace": "fr16rest", "conversation_id": "", "interaction_id": "itx-x", "choice": "approve",
    }).json()
    assert "no longer awaiting" in r["reply"].lower()
    assert _session_files("fr16rest") == []


# --- AC-7: the UI renders a visually distinct card ----------------------------


def test_ac7_ui_card_renders_distinct_in_chat_message(isolated_workspace_root):
    # AC-7 (FR-7/FR-10): the UI turns an interaction into a distinct assistant-message card (HTML) that
    # rides inside the chat scroll. Its inline options are the proposals plus a constant "chat about it"
    # last, plus a ✕ decline; nothing is pre-selected — clicking is what submits (P8). Returns falsy for
    # None / non-blocking notifications.
    from app import ui

    # A clarification with 2 proposals -> inline option buttons = [proposals..., "chat about it"] + ✕.
    clar = {
        "interaction_id": "itx-2", "conversation_id": "c", "kind": "clarification",
        "prompt": "Pick an approach",
        "options": [{"id": "opt-1", "label": "Ingest audit"}, {"id": "opt-2", "label": "Wiki sweep"}],
        "timeout_seconds": 30,
    }
    card = ui._card_html(clar)
    assert "itx-card" in card and "data-itx-id='itx-2'" in card
    assert "Pick an approach" in card
    # The choice rides in the element id (gr.Chatbot's DOMPurify strips data-*, keeps id) — the JS
    # bridge reads id="itx-opt-<choice>".
    assert "id='itx-opt-opt-1'" in card and "Ingest audit" in card
    assert "id='itx-opt-opt-2'" in card and "Wiki sweep" in card
    assert f"id='itx-opt-{ui.CHAT_ABOUT_IT[1]}'" in card and ui.CHAT_ABOUT_IT[0] in card
    assert "id='itx-opt-decline'" in card         # ✕ decline (FR-14)
    # spec 008 FR-9/D11: countdown seeded from text; remaining is a class + the timer id is scoped
    # per interaction so the JS reads only the live card and can't self-retrigger an expire loop.
    assert "class='itx-remaining'>30<" in card
    assert "id='itx-timer-itx-2'" in card

    # Approval (1 proposal) still gets the constant "chat about it" as the final option (FR-7).
    appr = {
        "interaction_id": "itx-1", "conversation_id": "c", "kind": "approval",
        "prompt": "Proceed?", "options": [{"id": "approve", "label": "Proceed with this plan"}],
        "timeout_seconds": 30,
    }
    appr_card = ui._card_html(appr)
    assert "id='itx-opt-approve'" in appr_card and "Proceed with this plan" in appr_card
    assert f"id='itx-opt-{ui.CHAT_ABOUT_IT[1]}'" in appr_card

    assert ui._card_html(None) is None
    # notifications never block (D10) -> no card
    assert ui._card_html({"kind": "notification", "prompt": "busy", "options": []}) is None


# --- AC-8: durable & recoverable after restart --------------------------------


def test_ac8_pending_interaction_survives_restart(client, isolated_workspace_root):
    # AC-8 (FR-11/P1): a pending interaction is recoverable by a brand-new client over the same disk
    # and can still be answered.
    from fastapi.testclient import TestClient

    from app.api import app

    first = _consequential_chat(client, "create a workspace named ac8ws")
    cid, itx_id = first["conversation_id"], first["interaction"]["interaction_id"]

    fresh = TestClient(app)  # simulate a service restart
    recovered = fresh.get("/api/chat/interaction", params={"conversation_id": cid}).json()
    assert recovered is not None and recovered["interaction_id"] == itx_id

    done = fresh.post("/api/chat/interaction", json={
        "conversation_id": cid, "interaction_id": itx_id, "choice": "approve",
    }).json()
    assert done["executed"] is True
    assert (isolated_workspace_root / "ac8ws" / "vault" / "wiki").is_dir()


# --- AC-9: REST parity --------------------------------------------------------


def test_ac9_interaction_protocol_present_on_rest(client):
    # AC-9 (FR-12/P9): the request (GET), response (POST), and streamed response are all REST routes,
    # so a machine caller has the same protocol the UI uses.
    from app.api import app

    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/api/chat/interaction" in paths
    assert "/api/chat/interaction/stream" in paths


# --- AC-10: capture into the sessions record ----------------------------------


def test_ac10_interaction_captured_in_sessions_record(client, isolated_workspace_root, session_file):
    # AC-10 (FR-13/P6): the request, its options, and the resolution are all recorded in sessions/.
    first = _consequential_chat(client, "create a workspace named ac10ws")
    cid, itx_id = first["conversation_id"], first["interaction"]["interaction_id"]
    client.post("/api/chat/interaction", json={
        "conversation_id": cid, "interaction_id": itx_id, "choice": "approve",
    })
    text = session_file(isolated_workspace_root / "_default_", cid).read_text(encoding="utf-8")
    assert "[approval]" in text            # request captured with its kind
    assert "[resolved]" in text            # resolution captured
    assert "approve" in text


# --- AC-11: idempotent, id-scoped responses -----------------------------------


def test_ac11_unknown_and_double_response_rejected_no_side_effects(client, isolated_workspace_root):
    # AC-11 (FR-16): unknown ids and a second response are rejected with no side effects — no double
    # execution, no post-resolution execution.
    first = _consequential_chat(client, "create a workspace named ac11ws")
    cid, itx_id = first["conversation_id"], first["interaction"]["interaction_id"]

    unknown = client.post("/api/chat/interaction", json={
        "conversation_id": cid, "interaction_id": "itx-does-not-exist", "choice": "approve",
    }).json()
    assert "no longer awaiting" in unknown["reply"]

    ok = client.post("/api/chat/interaction", json={
        "conversation_id": cid, "interaction_id": itx_id, "choice": "approve",
    }).json()
    assert ok["executed"] is True

    again = client.post("/api/chat/interaction", json={
        "conversation_id": cid, "interaction_id": itx_id, "choice": "approve",
    }).json()
    assert again["executed"] is False               # not executed a second time
    assert "no longer awaiting" in again["reply"]
    assert (isolated_workspace_root / "ac11ws" / "vault" / "wiki").is_dir()


# --- AC-12: one blocking interaction at a time; notifications alongside --------


def test_ac12_one_blocking_interaction_outstanding(client, isolated_workspace_root):
    # AC-12 (FR-15): a second blocking interaction is refused while one is pending; a non-blocking
    # notification may still be raised and does not displace the pending blocking one.
    capabilities.create_workspace("demo")
    first = capabilities.create_interaction("demo", None, "approval", "Do it?", ["Yes"])

    with pytest.raises(WorkspaceError):
        capabilities.create_interaction("demo", first.conversation_id, "clarification", "pick", ["A", "B"])

    note = capabilities.create_interaction("demo", first.conversation_id, "notification", "working…")
    assert note.kind == "notification"

    pending = capabilities.get_pending_interaction("demo", first.conversation_id)
    assert pending is not None and pending.interaction_id == first.interaction_id
