# Tasks: Expose the capability layer to the agent as MCP tools (006)

Ordered build for feature `006-mcp-capability-tools`. Each task cites the spec requirement it
satisfies. See [`spec.md`](spec.md) and [`plan.md`](plan.md).

- [x] **T001 — Specs (spec-first):** write `spec.md`, `plan.md`, `tasks.md`; update [[13-api]]
  (MCP tool surface + blacklist governance + workspace binding + AC). *(spec 006 all FR)*
- [x] **T002 — Config:** add `config.mcp_tool_blacklist()` (env `LEADER_MCP_TOOL_BLACKLIST`,
  default `{chat, upload, create_workspace}`; `""` → empty set; unset → default). *(FR-1)*
- [x] **T003 — Agent registry:** add `ToolSpec`, `_capability_tool_specs(selector, citations)`
  (every capability tool, workspace-bound; chat structurally excluded), `_selected_specs(specs,
  blacklist)`, `_allowed_tool_names(specs)`. *(FR-3, FR-4, FR-5, FR-6)*
- [x] **T004 — Agent wiring:** rewrite `_build_server` to filter by `config.mcp_tool_blacklist()`
  and register selected specs via `@tool`; set `allowed_tools=[*_NATIVE_TOOLS,
  *_allowed_tool_names(selected)]`; drop the old `_tool_names`; update the module docstring.
  *(FR-2, FR-8)*
- [x] **T005 — Tests:** `tests/test_agent_mcp_tools.py` — default tool-name set (AC-1); chat
  never registered with empty blacklist (AC-2); config-driven removal of an in-registry tool
  (AC-3); workspace-binding ignores an `args` workspace (AC-4); `ingest`/`import_skill` handlers
  mutate + commit the active workspace (AC-5); REST routes unchanged (AC-7); opt-in live
  "list skills" (AC-6). Run `uv run --extra dev pytest` green. *(AC-1..AC-7)*
