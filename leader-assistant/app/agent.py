"""Agent runtime adapter (spec 002 T021/T022; D3 · spec 005 FR-8/9/10 · spec 006).

The assistant reaches the model through ``claude-agent-sdk``. Its in-process MCP server
**mirrors the whole capability layer** (spec 006 FR-3): every capability function is an
agent tool, minus a governed exclusion set. The chat surface (``ask``/``ask_stream``) is
**structurally excluded** — never registered — so the agent cannot re-enter chat and
recurse (spec 006 D4). A **config-driven blacklist** (``config.mcp_tool_blacklist()``,
default ``{chat, upload, create_workspace}``) withholds further tools; ``upload`` stays
human-only so the agent cannot write ``vault/raw/`` (P2), and ``create_workspace`` keeps
the agent scoped to its active workspace (spec 006 D2/D3). Every tool is **workspace-bound**
— the workspace argument is injected from the run context, not from tool args (spec 006
FR-6). ``query`` remains the cited way to browse knowledge (FR-5).

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

from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Awaitable, Callable

from . import models, vault

_SERVER = "leader"

# Native tools granted for skill execution (spec 005 FR-9), alongside the MCP tools.
_NATIVE_TOOLS = ["Skill", "Bash", "Read", "Write", "Edit", "Glob", "Grep"]


class AgentUnavailable(RuntimeError):
    """Raised when the agent runtime cannot be reached (missing CLI/credentials)."""


@dataclass
class ToolSpec:
    """One agent MCP tool: its name/description/schema and an async handler (spec 006).

    The handler closes over the run's active workspace selector, so the tool is
    workspace-bound (FR-6) and unit-testable without the SDK.
    """

    name: str
    description: str
    schema: dict
    handler: Callable[[dict], Awaitable[dict]]


def _ok(text: str) -> dict:
    """SDK tool-content shape for a text result."""
    return {"content": [{"type": "text", "text": text}]}


def _capability_tool_specs(
    workspace_selector: str | None, citations: list[models.Citation]
) -> list[ToolSpec]:
    """Build an agent tool for every exposable capability (spec 006 FR-3/FR-4).

    Pure and SDK-free: handlers call ``capabilities`` directly. Every handler injects
    ``workspace_selector`` and ignores any ``workspace`` in tool args (the sandbox,
    FR-6). The chat surface is deliberately absent (structural exclusion, D4). Mutating
    tools (``ingest``/``import_skill``) execute directly (FR-4, spec 005 D1).
    """
    from . import capabilities  # lazy import to avoid an agent<->capabilities cycle

    async def query_h(args: dict) -> dict:
        ans = capabilities.query(
            models.QueryRequest(workspace=workspace_selector, question=args["question"])
        )
        citations.extend(ans.citations)  # surfaced to the caller for the reply (FR-5)
        lines = [ans.answer, ""]
        for c in ans.citations:
            lines.append(f"- {c.page}: {c.excerpt}")
        return _ok("\n".join(lines))

    async def spec_read_h(args: dict) -> dict:
        try:
            text = capabilities.spec_read(args["path"], workspace_selector)
        except Exception as e:  # noqa: BLE001 — surface as tool text, not a crash
            return _ok(f"error: {e}")
        return _ok(text[:4000])

    async def plan_h(args: dict) -> dict:
        p = capabilities.plan(
            models.PlanRequest(workspace=workspace_selector, request=args["request"])
        )
        steps = "\n".join(f"{s.order}. {s.action} — {s.rationale}" for s in p.steps)
        return _ok(f"risk={p.risk} requires_approval={p.requires_approval}\n{steps}")

    async def list_workspaces_h(args: dict) -> dict:
        return _ok(capabilities.list_workspaces().model_dump_json(indent=2))

    async def get_workspace_info_h(args: dict) -> dict:
        return _ok(capabilities.get_workspace_info(workspace_selector).model_dump_json(indent=2))

    async def lint_h(args: dict) -> dict:
        return _ok(capabilities.lint(workspace_selector).model_dump_json(indent=2))

    async def wiki_tree_h(args: dict) -> dict:
        return _ok(capabilities.wiki_tree(workspace_selector).model_dump_json(indent=2))

    async def list_conversations_h(args: dict) -> dict:
        return _ok(capabilities.list_conversations(workspace_selector).model_dump_json(indent=2))

    async def get_conversation_h(args: dict) -> dict:
        try:
            detail = capabilities.get_conversation(workspace_selector, args["conversation_id"])
        except Exception as e:  # noqa: BLE001
            return _ok(f"error: {e}")
        return _ok(detail.model_dump_json(indent=2))

    async def conversation_status_h(args: dict) -> dict:
        status = capabilities.conversation_status(workspace_selector, args["conversation_id"])
        return _ok(status.model_dump_json(indent=2))

    async def list_available_skills_h(args: dict) -> dict:
        return _ok(capabilities.list_available_skills(workspace_selector).model_dump_json(indent=2))

    async def list_installed_skills_h(args: dict) -> dict:
        return _ok(capabilities.list_installed_skills(workspace_selector).model_dump_json(indent=2))

    async def ingest_h(args: dict) -> dict:
        try:
            report = capabilities.ingest(
                models.IngestRequest(
                    workspace=workspace_selector,
                    title=args["title"],
                    content=args["content"],
                    provenance=args.get("provenance") or "notes",
                )
            )
        except Exception as e:  # noqa: BLE001
            return _ok(f"error: {e}")
        return _ok(report.model_dump_json(indent=2))

    async def import_skill_h(args: dict) -> dict:
        try:
            report = capabilities.import_skill(workspace_selector, args["name"])
        except Exception as e:  # noqa: BLE001
            return _ok(f"error: {e}")
        return _ok(report.model_dump_json(indent=2))

    return [
        ToolSpec("query", "Search the workspace and return an answer with citations. The primary way to browse project knowledge.", {"question": str}, query_h),
        ToolSpec("spec_read", "Read the raw Markdown of a known workspace page by its relative path.", {"path": str}, spec_read_h),
        ToolSpec("plan", "Produce a step-by-step plan for a work request; consequential work is flagged for approval.", {"request": str}, plan_h),
        ToolSpec("list_workspaces", "List known workspaces (names, root, default).", {}, list_workspaces_h),
        ToolSpec("get_workspace_info", "Inspect the active workspace: name, path, whether scaffolded, and page count.", {}, get_workspace_info_h),
        ToolSpec("lint", "Run hygiene checks (orphan/short pages) on the active workspace.", {}, lint_h),
        ToolSpec("wiki_tree", "Browse the active workspace's vault/wiki/ tree (navigation only).", {}, wiki_tree_h),
        ToolSpec("list_conversations", "List prior conversations in the active workspace.", {}, list_conversations_h),
        ToolSpec("get_conversation", "Read one conversation's full turns by its id.", {"conversation_id": str}, get_conversation_h),
        ToolSpec("conversation_status", "Report whether a conversation has a turn in progress on the server (running) and whether it exists.", {"conversation_id": str}, conversation_status_h),
        ToolSpec("list_available_skills", "List skills available to install from the shared library, each with a description and an installed flag.", {}, list_available_skills_h),
        ToolSpec("list_installed_skills", "List skills currently installed in the active workspace.", {}, list_installed_skills_h),
        ToolSpec("ingest", "Ingest a source into the workspace: writes a vault/wiki/sources summary, updates the portal, appends the log, and commits. Never writes vault/raw/.", {"title": str, "content": str, "provenance": str}, ingest_h),
        ToolSpec("import_skill", "Reference-link a shared-library skill into the active workspace and commit.", {"name": str}, import_skill_h),
    ]


def _selected_specs(
    workspace_selector: str | None,
    citations: list[models.Citation],
    blacklist: set[str],
) -> list[ToolSpec]:
    """Capability tools minus the blacklist (spec 006 FR-2). Chat is already absent (D4)."""
    return [s for s in _capability_tool_specs(workspace_selector, citations) if s.name not in blacklist]


def _allowed_tool_names(specs: list[ToolSpec]) -> list[str]:
    """Fully-qualified MCP tool names for ``allowed_tools`` (spec 006 FR-8)."""
    return [f"mcp__{_SERVER}__{s.name}" for s in specs]


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


def _build_server(specs: list[ToolSpec]):
    """Build an in-process MCP server from selected capability tool specs (spec 006)."""
    from claude_agent_sdk import create_sdk_mcp_server, tool

    tools = [tool(s.name, s.description, s.schema)(s.handler) for s in specs]
    return create_sdk_mcp_server(_SERVER, "1.0.0", tools=tools)


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

    # Mirror the capability layer minus the blacklist; derive the server and
    # allowed_tools from the SAME selected set so registration and permission agree
    # (spec 006 FR-3/FR-8). Chat is never in the set (structural exclusion, D4).
    specs = _selected_specs(workspace_selector, citations, config.mcp_tool_blacklist())
    server = _build_server(specs)
    opts = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model="sonnet",
        mcp_servers={_SERVER: server},
        allowed_tools=[*_NATIVE_TOOLS, *_allowed_tool_names(specs)],
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
