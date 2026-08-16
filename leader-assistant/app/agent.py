"""Agent runtime adapter (spec 002 T021/T022; D3 · spec 005 FR-8/9/10).

The assistant reaches the model through ``claude-agent-sdk``. It always has the
in-process capability MCP tools (``query``/``spec_read``/``plan``), where ``query``
remains the cited, parity-preserving way to browse knowledge (FR-2).

**Skill execution (feature 005) deliberately expands the tool set.** To let the agent
discover and run installed skills, it is granted real ``Skill``/``Bash``/``Read``/
``Write``/``Edit``/``Glob``/``Grep`` tools, scoped to the active workspace via ``cwd``
and ``add_dirs`` and run under ``bypassPermissions``. This reverses the citations-only
browse boundary of feature 002 D3 *for skill execution* (spec 005 D3). Skill discovery
requires ``setting_sources=["project"]`` (an empty list disables skills entirely).

Because ``can_use_tool`` is not consulted under ``bypassPermissions``, ``vault/raw/``
immutability (P2) is enforced for the agent by a **PreToolUse raw-guard hook**
(``_raw_guard_decision``); the per-workspace git repo is the backstop for the residual
Bash-write risk (spec 005 D3).
"""

from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator

from . import models, vault

_SERVER = "leader"

# Native tools granted for skill execution (spec 005 FR-9), alongside the MCP tools.
_NATIVE_TOOLS = ["Skill", "Bash", "Read", "Write", "Edit", "Glob", "Grep"]


class AgentUnavailable(RuntimeError):
    """Raised when the agent runtime cannot be reached (missing CLI/credentials)."""


def _tool_names() -> list[str]:
    return [f"mcp__{_SERVER}__{t}" for t in ("query", "spec_read", "plan")]


def _raw_guard_decision(workspace_path: Path, tool_name: str, tool_input: dict) -> str | None:
    """Pure raw-guard: return a deny reason if a tool call would write vault/raw/, else None.

    Enforces P2 for the autonomous agent (spec 005 FR-10). Path-based for the file tools;
    heuristic for Bash (a shell redirect can still evade this — git is the backstop, D3).
    """
    if tool_name in ("Write", "Edit", "NotebookEdit"):
        raw = tool_input.get("file_path") or tool_input.get("notebook_path")
        if not raw:
            return None
        target = Path(raw)
        if not target.is_absolute():
            target = workspace_path / target
        try:
            vault.guard_write_path(workspace_path, target)
        except vault.WorkspaceError as e:
            return str(e)
        return None
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if "vault/raw" in command and any(
            tok in command
            for tok in (">", "tee ", "cp ", "mv ", "rm ", "truncate", "sed -i", "dd ", "mkdir", "touch ")
        ):
            return "vault/raw/ is immutable; refusing Bash write into vault/raw/ (spec 005 FR-10)"
    return None


def _raw_guard_hook(workspace_path: Path):
    """Build the PreToolUse hook callback that applies ``_raw_guard_decision``."""

    async def hook(input_data: dict, tool_use_id: str | None, context) -> dict:  # noqa: ANN001
        reason = _raw_guard_decision(
            workspace_path, input_data.get("tool_name", ""), input_data.get("tool_input", {}) or {}
        )
        if reason:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        return {}

    return hook


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
    workspace_path: Path,
    resume_sid: str | None,
    citations: list[models.Citation],
) -> AsyncIterator[tuple[str, str | None]]:
    """Stream (accumulated_reply, sdk_session_id) as the agent produces text.

    Mirrors the archived streaming pattern (query → init → text deltas → result). Runs
    workspace-scoped with skill discovery + native tools (spec 005 FR-8/9) and the
    raw-guard PreToolUse hook (FR-10).
    """
    try:
        from claude_agent_sdk import (
            ClaudeAgentOptions,
            CLINotFoundError,
            HookMatcher,
            ResultMessage,
            StreamEvent,
            SystemMessage,
            query,
        )
    except ImportError as e:  # pragma: no cover
        raise AgentUnavailable(str(e)) from e

    from . import config

    server = _build_server(workspace_selector, citations)
    opts = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model="sonnet",
        mcp_servers={_SERVER: server},
        allowed_tools=[*_NATIVE_TOOLS, *_tool_names()],
        permission_mode="bypassPermissions",
        setting_sources=["project"],  # MUST include a scope or skills are disabled (spec 005 risk 1)
        skills="all",
        cwd=str(workspace_path),
        add_dirs=[str(workspace_path), str(config.skills_library_root())],
        hooks={"PreToolUse": [HookMatcher(hooks=[_raw_guard_hook(workspace_path)])]},
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
