# Implementation Plan: Expose the capability layer to the agent as MCP tools (006)

**Feature ID:** `006-mcp-capability-tools` · **Status:** Draft · **Created:** 2026-08-17

Companion to [`spec.md`](spec.md). Records the **decided** design. Cite requirements as
`spec 006 FR-N` in code comments.

## Context

`app/agent.py:_build_server` currently hand-registers three MCP tools (`query`, `spec_read`,
`plan`) closing over `workspace_selector`. All other capabilities in `app/capabilities.py` are
REST-only. This feature turns `_build_server` into a **registry** that mirrors the capability
layer minus a config blacklist, keeps every tool **workspace-bound**, and derives
`allowed_tools` from the same selected set.

## Design

### Tool registry (pure, testable)

Introduce a small internal registry so the tool set and its filtering are unit-testable without
the SDK:

- `ToolSpec` — a lightweight record `{name, description, schema: dict, handler}` where `handler`
  is an `async (args: dict) -> dict` that (a) injects the active workspace and (b) returns the
  SDK tool-content shape `{"content": [{"type": "text", "text": ...}]}`.
- `_capability_tool_specs(workspace_selector, citations) -> list[ToolSpec]` — builds every
  capability tool, each closing over `workspace_selector` (the sandbox, FR-6). This function
  does **not** import the SDK, so tests can call it and its handlers directly.
- `_selected_specs(specs, blacklist) -> list[ToolSpec]` — drops specs whose `name` is in the
  blacklist (FR-2). `ask`/`chat` is never in the registry at all (structural exclusion, FR-3/D4).
- `_build_server(...)` — imports `create_sdk_mcp_server` + `tool`, wraps each selected spec's
  handler with `@tool(name, description, schema)`, returns the server.
- `_allowed_tool_names(specs) -> list[str]` — `[f"mcp__{_SERVER}__{s.name}" for s in specs]`,
  used for `ClaudeAgentOptions.allowed_tools` alongside `_NATIVE_TOOLS` (FR-8).

### The tools (workspace-bound handlers → capability calls)

Read-only (serialise the pydantic result to JSON text):
- `query` (keep citation surfacing, FR-5), `spec_read`, `plan` (existing behaviour retained)
- `list_workspaces` → `capabilities.list_workspaces()`
- `get_workspace_info` → `capabilities.get_workspace_info(workspace_selector)`
- `lint` → `capabilities.lint(workspace_selector)`
- `wiki_tree` → `capabilities.wiki_tree(workspace_selector)`
- `list_conversations` → `capabilities.list_conversations(workspace_selector)`
- `get_conversation` (`{conversation_id}`) → `capabilities.get_conversation(workspace_selector, id)`
- `list_available_skills` → `capabilities.list_available_skills(workspace_selector)`
- `list_installed_skills` → `capabilities.list_installed_skills(workspace_selector)`

Mutating (direct execution, FR-4/D1):
- `ingest` (`{title, content, provenance?}`) → `capabilities.ingest(IngestRequest(workspace=selector, …))`
- `import_skill` (`{name}`) → `capabilities.import_skill(workspace_selector, name)`

Excluded: `create_workspace`, `upload` (default blacklist); `ask`/`chat`/`ask_stream`
(structural, never in registry).

**Binding rule (FR-6/D6):** handlers ignore any `workspace` key in `args` and always pass
`workspace_selector`. Schemas do not declare a `workspace` field.

**Error handling:** handlers wrap capability calls and, on `WorkspaceError`/`Exception`, return
`{"content": [{"type": "text", "text": f"error: {e}"}]}` (as `spec_read` already does) so a bad
call surfaces as tool text, not a crash.

## Code changes

### `app/config.py`
- Add `mcp_tool_blacklist() -> set[str]`: parse env `LEADER_MCP_TOOL_BLACKLIST` (comma-separated,
  strip whitespace, drop empties); default `{"chat", "upload", "create_workspace"}`. An env value
  of `""` yields an **empty** set (operator explicitly opts everything in) — distinct from unset,
  which yields the default. (spec 006 FR-1)

### `app/agent.py`
- Add `ToolSpec` (dataclass), `_capability_tool_specs`, `_selected_specs`, `_allowed_tool_names`.
- Rewrite `_build_server` to build specs, filter by `config.mcp_tool_blacklist()`, wrap with
  `@tool`, and register. Keep the special `query` handler (citation surfacing).
- In `run_stream`, set `allowed_tools=[*_NATIVE_TOOLS, *_allowed_tool_names(selected)]` from the
  same selected set (FR-8). Remove the old `_tool_names()` (superseded) or keep as a thin shim
  used by tests — prefer removing and updating references.
- Update the module docstring: the agent now mirrors the whole capability layer minus the
  blacklist; chat is structurally excluded (recursion); tools are workspace-bound.

### No change to `app/api.py`, `app/models.py`, `app/capabilities.py`
- REST is untouched (FR-7). Capabilities are reused as-is. (If a tiny import cycle appears,
  import `capabilities` lazily inside handlers as the existing code already does.)

## Tests (`tests/`, offline + deterministic)

New `tests/test_agent_mcp_tools.py` — exercises the registry directly (no live agent):
- **AC-1:** `_capability_tool_specs(...)` filtered by the default blacklist yields exactly the
  expected name set; asserts `create_workspace`, `upload`, `ask`/`chat` are absent and the parity
  tools present.
- **AC-2:** with `LEADER_MCP_TOOL_BLACKLIST=""`, `chat`/`ask` is still absent (structural).
- **AC-3:** adding `lint` to the env blacklist drops `lint` from both the specs and
  `_allowed_tool_names`; clearing the default re-admits `upload`/`create_workspace` **only if**
  their specs exist (create_workspace/upload are not in the registry by design → they stay absent;
  assert the blacklist mechanism via a registered tool like `lint`). *(Adjust AC-3 test to prove
  config-driven removal using an in-registry tool; document that upload/create_workspace are
  simply never built.)*
- **AC-4:** call the `get_workspace_info` / `ingest` handler with `{"workspace": "other", …}` and
  assert it operated on the bound workspace, not "other".
- **AC-5:** the `ingest` handler creates `vault/wiki/sources/…` + a commit; the `import_skill`
  handler (using the `skills_library` fixture) creates the reference-link + commit.
- Handlers are `async`; drive them with `asyncio`/`anyio` as the suite already does for chat.
- **AC-7:** a smoke assertion that the REST app still exposes all prior routes (reuse the
  existing route-registration checks).
- **Opt-in live test** (`LEADER_LIVE_AGENT=1`): a chat turn "what skills can I install?" returns
  the catalog via the agent (AC-6).

Run `uv run --extra dev pytest` green.

## Key risks

1. **`allowed_tools` must match the registered set** — if a tool is registered but not allowed
   (or vice-versa) it silently won't be callable. Derive both from one selected list (FR-8).
2. **Import cycle** `agent → capabilities → agent`? Handlers import `capabilities` lazily (the
   existing pattern) to avoid it.
3. **Workspace-binding leak** — a handler that forwards `args["workspace"]` would break the
   sandbox. Handlers must ignore it (FR-6); covered by AC-4.
4. **create_workspace/upload are never in the registry**, so the "blacklist re-admits them" idea
   doesn't apply — the AC-3 test must prove config-driven removal with an *in-registry* tool.
