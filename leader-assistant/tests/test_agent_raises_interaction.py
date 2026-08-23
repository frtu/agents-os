"""The agent can raise its own interaction cards mid-turn (spec 008 FR-18 / AC-14).

Offline & deterministic: no live agent runtime. We exercise the new `request_interaction`
MCP tool's handler directly and, for the surfacing path, monkeypatch `agent.run_stream`
with a fake async generator that raises a card exactly as the real tool handler would.
"""

from __future__ import annotations

import asyncio

from app import agent, capabilities, config, models


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
                              citations, conversation_id=None, interactions=None):
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
