"""Agent runtime adapter (spec 002 T021/T022; D3).

The assistant reaches the model through ``claude-agent-sdk`` and browses
knowledge **only** by calling the capability layer, exposed here as in-process
MCP tools. There is deliberately no raw ``Read``/``Glob``/``Grep`` browse tool:
every knowledge lookup goes through ``query`` (which returns citations), keeping
chat inside the parity boundary (P9) and every answer verifiable (FR-2).

No write tool is exposed to the agent in this MVP — mutations are gated behind
the plan/approval flow in ``capabilities.ask`` (FR-5, FR-11), so the write-guard
(T022) is enforced by construction: the agent simply has no way to write.
"""

from __future__ import annotations

from typing import AsyncIterator

from . import models

_SERVER = "leader"


class AgentUnavailable(RuntimeError):
    """Raised when the agent runtime cannot be reached (missing CLI/credentials)."""


def _tool_names() -> list[str]:
    return [f"mcp__{_SERVER}__{t}" for t in ("query", "spec_read", "plan")]


def _build_server(workspace_selector: str | None, citations: list[models.Citation]):
    """Build an in-process MCP server whose tools are the capability functions."""
    from claude_agent_sdk import create_sdk_mcp_server, tool

    from . import capabilities

    @tool("query", "Search the workspace and return an answer with citations. The ONLY way to browse project knowledge.", {"question": str})
    async def query_tool(args: dict) -> dict:
        ans = capabilities.query(models.QueryRequest(workspace=workspace_selector, question=args["question"]))
        citations.extend(ans.citations)  # surfaced to the caller for the reply
        lines = [ans.answer, ""]
        for c in ans.citations:
            lines.append(f"- {c.page}: {c.excerpt}")
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    @tool("spec_read", "Read the raw Markdown of a known workspace page by its relative path.", {"path": str})
    async def spec_read_tool(args: dict) -> dict:
        try:
            text = capabilities.spec_read(args["path"], workspace_selector)
        except Exception as e:  # noqa: BLE001 — surface as tool text, not a crash
            return {"content": [{"type": "text", "text": f"error: {e}"}]}
        return {"content": [{"type": "text", "text": text[:4000]}]}

    @tool("plan", "Produce a step-by-step plan for a work request; consequential work is flagged for approval.", {"request": str})
    async def plan_tool(args: dict) -> dict:
        p = capabilities.plan(models.PlanRequest(workspace=workspace_selector, request=args["request"]))
        steps = "\n".join(f"{s.order}. {s.action} — {s.rationale}" for s in p.steps)
        text = f"risk={p.risk} requires_approval={p.requires_approval}\n{steps}"
        return {"content": [{"type": "text", "text": text}]}

    return create_sdk_mcp_server(_SERVER, "1.0.0", tools=[query_tool, spec_read_tool, plan_tool])


async def run_stream(
    system_prompt: str,
    message: str,
    workspace_selector: str | None,
    resume_sid: str | None,
    citations: list[models.Citation],
) -> AsyncIterator[tuple[str, str | None]]:
    """Stream (accumulated_reply, sdk_session_id) as the agent produces text.

    Mirrors the archived streaming pattern (query → init → text deltas →
    result) but re-pointed at the capability layer (D3).
    """
    try:
        from claude_agent_sdk import (
            ClaudeAgentOptions,
            CLINotFoundError,
            ResultMessage,
            StreamEvent,
            SystemMessage,
            query,
        )
    except ImportError as e:  # pragma: no cover
        raise AgentUnavailable(str(e)) from e

    server = _build_server(workspace_selector, citations)
    opts = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model="sonnet",
        mcp_servers={_SERVER: server},
        allowed_tools=_tool_names(),
        permission_mode="default",
        setting_sources=[],
        include_partial_messages=True,
        resume=resume_sid,
    )

    reply, sid = "", resume_sid
    try:
        async for m in query(prompt=message, options=opts):
            if isinstance(m, SystemMessage) and getattr(m, "subtype", "") == "init":
                sid = m.data.get("session_id", sid)
            elif isinstance(m, StreamEvent):
                ev = m.event
                if ev.get("type") == "content_block_delta" and ev.get("delta", {}).get("type") == "text_delta":
                    reply += ev["delta"]["text"]
                    yield reply, sid
            elif isinstance(m, ResultMessage):
                sid = getattr(m, "session_id", None) or sid
    except CLINotFoundError as e:
        raise AgentUnavailable("claude CLI not found") from e
    except Exception as e:  # noqa: BLE001 — treat runtime failures as unavailability
        raise AgentUnavailable(str(e)) from e
    yield reply, sid
