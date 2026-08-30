"""The agent can raise its own interaction cards mid-turn (spec 008 FR-18 / AC-14).

Offline & deterministic: no live agent runtime. We exercise the new `request_interaction`
MCP tool's handler directly and, for the surfacing path, monkeypatch `agent.run_stream`
with a fake async generator that raises a card exactly as the real tool handler would.
"""

from __future__ import annotations

import asyncio

from app import agent, capabilities, config, conversation, models


def _request_interaction_handler(selector, conversation_id, interactions):
    specs = agent._capability_tool_specs(selector, [], conversation_id, interactions)
    return next(s for s in specs if s.name == "request_interaction").handler


# --- FR-18: the tool is registered and live (not blacklisted) -----------------


def test_request_interaction_tool_registered_and_not_blacklisted():
    specs = agent._selected_specs(None, [], config.mcp_tool_blacklist())
    assert "request_interaction" in {s.name for s in specs}
    assert "request_interaction" not in config.mcp_tool_blacklist()


# --- FR-18/FR-11: a clarification the agent raises is appended + persisted -----


def test_handler_raises_clarification_appends_and_persists(isolated_workspace_root):
    capabilities.create_workspace("demo")
    raised: list[models.Interaction] = []
    handler = _request_interaction_handler("demo", None, raised)

    result = asyncio.run(handler(
        {"kind": "clarification", "prompt": "Pick an approach", "options": '["Ingest audit", "Wiki sweep"]'}
    ))
    assert not result["content"][0]["text"].startswith("error:")

    assert len(raised) == 1 and raised[0].kind == "clarification"
    assert [o.label for o in raised[0].options] == ["Ingest audit", "Wiki sweep"]
    # Blocking kinds are durable (FR-11): a fresh read finds the pending interaction.
    pending = capabilities.get_pending_interaction("demo", raised[0].conversation_id)
    assert pending is not None and pending.interaction_id == raised[0].interaction_id


def test_handler_notification_appends_but_does_not_persist(isolated_workspace_root):
    capabilities.create_workspace("demo")
    raised: list[models.Interaction] = []
    handler = _request_interaction_handler("demo", None, raised)

    asyncio.run(handler({"kind": "notification", "prompt": "working…", "options": "[]"}))
    assert len(raised) == 1 and raised[0].kind == "notification"
    # Notifications are non-blocking (FR-3): nothing persisted as pending.
    assert capabilities.get_pending_interaction("demo", raised[0].conversation_id) is None


# --- FR-18: the agent cannot self-raise an approval (stays plan-first) ---------


def test_handler_rejects_approval_kind(isolated_workspace_root):
    capabilities.create_workspace("demo")
    handler = _request_interaction_handler("demo", None, [])
    result = asyncio.run(handler({"kind": "approval", "prompt": "Do it?", "options": '["Yes"]'}))
    assert result["content"][0]["text"].startswith("error:")


def test_handler_rejects_malformed_options_json(isolated_workspace_root):
    capabilities.create_workspace("demo")
    handler = _request_interaction_handler("demo", None, [])
    result = asyncio.run(handler({"kind": "clarification", "prompt": "?", "options": "not json"}))
    assert result["content"][0]["text"].startswith("error:")


# --- FR-18/AC-1: the routine turn surfaces an agent-raised card ----------------


def test_routine_turn_surfaces_agent_raised_clarification(isolated_workspace_root, monkeypatch):
    capabilities.create_workspace("demo")

    async def fake_run_stream(system_prompt, message, selector, wpath, resume_sid,
                              citations, conversation_id=None, interactions=None, trust=False,
                              naming=None):
        # Mimic the model calling request_interaction (append the raised card), then answering.
        itx = capabilities.create_interaction(
            selector, conversation_id, "clarification", "Pick an approach", ["A", "B"]
        )
        if interactions is not None:
            interactions.append(itx)
        yield "Here are two ways to go.", resume_sid

    monkeypatch.setattr(agent, "run_stream", fake_run_stream)

    last = None
    async def _drive():
        nonlocal last
        async for d in capabilities.ask_stream("demo", "run multi-agent mode"):
            last = d
    asyncio.run(_drive())

    assert last is not None and last.done is True
    assert last.interaction is not None
    assert last.interaction.kind == "clarification"
    assert [o.label for o in last.interaction.options] == ["A", "B"]

# --- FR-11/AC-15: the card outlives the rest of the turn's own writes ----------


def test_ac15_agent_raised_card_survives_the_turn_and_is_answerable(
    isolated_workspace_root, monkeypatch
):
    """A clarification raised mid-stream stayed on screen but could not be answered.

    `create_interaction` loads its own `Conversation` to persist the card, so the turn's instance —
    loaded before the stream — knew nothing about it. The turn then wrote its session id, and
    rendering the frontmatter from that stale instance erased `Pending-interaction`, leaving the
    click to be rejected with "no longer awaiting a response". The new session id is what arms the
    bug, so this test yields one.
    """
    capabilities.create_workspace("demo")

    async def raising_run_stream(system_prompt, message, selector, wpath, resume_sid,
                                 citations, conversation_id=None, interactions=None, trust=False,
                                 naming=None):
        itx = capabilities.create_interaction(
            selector, conversation_id, "clarification", "How should the re-run be scoped?",
            ["Regenerate at P5", "Keep an audit trail", "Post-review only"],
        )
        if interactions is not None:
            interactions.append(itx)
        yield "Waiting for your selection.", "sdk-session-from-this-turn"

    monkeypatch.setattr(agent, "run_stream", raising_run_stream)

    card, cid = None, None
    async def _turn():
        nonlocal card, cid
        async for d in capabilities.ask_stream("demo", "Re run pre & post interview for Shaowen"):
            if d.done:
                card, cid = d.interaction, d.conversation_id
    asyncio.run(_turn())
    assert card is not None

    # The durable record is the source of truth (FR-11, P1) — and the session id landed too.
    pending = capabilities.get_pending_interaction("demo", cid)
    assert pending is not None and pending.interaction_id == card.interaction_id
    conv = conversation.load(isolated_workspace_root / "demo", cid)
    assert conv.sdk_session_id == "sdk-session-from-this-turn"

    async def plain_run_stream(system_prompt, message, selector, wpath, resume_sid,
                               citations, conversation_id=None, interactions=None, trust=False,
                               naming=None):
        yield "Regenerating as engineering-screen at P5.", resume_sid

    monkeypatch.setattr(agent, "run_stream", plain_run_stream)

    replies = []
    async def _answer():
        async for d in capabilities.respond_to_interaction_stream(
            "demo", cid, card.interaction_id, "opt-1"
        ):
            if d.done:
                replies.append(d.reply)
    asyncio.run(_answer())

    assert replies and "no longer awaiting" not in replies[0]
    assert replies[0] == "Regenerating as engineering-screen at P5."
    assert capabilities.get_pending_interaction("demo", cid) is None  # resolved, not left dangling
