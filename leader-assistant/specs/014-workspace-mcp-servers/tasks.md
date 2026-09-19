# Tasks: Per-workspace MCP servers with captured OAuth login (014)

Ordered build for feature `014-workspace-mcp-servers`. Each task cites the spec requirement it
satisfies. See [`spec.md`](spec.md) and [`plan.md`](plan.md).

- [x] **T001 — Specs (spec-first):** write `spec.md`, `plan.md`, `tasks.md`; update
  [[15-integrations]] (per-workspace MCP servers section) and [[03-workspace]] (add `.mcp.json`
  tracked + `.mcp-auth/` git-ignored to the layout). *(spec 014 all FR)*
- [x] **T002 — Config:** add `workspace_mcp_config_path`, `workspace_mcp_auth_dir`,
  `workspace_mcp_servers` (tolerant read of `.mcp.json`); add the four capabilities to
  `DEFAULT_MCP_TOOL_BLACKLIST`. *(FR-1, FR-6, FR-12)*
- [x] **T003 — Models:** `McpServerInfo`, `McpServerList`, `McpLoginInfo` in `app/models.py`.
  *(FR-3, FR-8)*
- [x] **T004 — Git-ignore:** add `.mcp-auth/` to `templates/_workspace_/.gitignore` (and ensure
  scaffolded workspaces ignore it); `.mcp.json` stays tracked. *(FR-7)*
- [x] **T005 — Capabilities:** `list_mcp_servers` (auto), `add_mcp_server` (reversible),
  `remove_mcp_server` (reversible), `login_mcp_server` (auto); name validation; `.mcp.json`
  writes via `_record_turn_effects` (log + commit); register all four in `EFFECTS`.
  *(FR-1..FR-5, FR-8, FR-9, FR-13, D5)*
- [x] **T006 — Agent wiring:** in `run_stream`, set `os.environ["CLAUDE_CONFIG_DIR"]` to the
  workspace `.mcp-auth/` and extend `allowed_tools` with `mcp__<name>__*` for each registered
  server. External tools stay under the PreToolUse gate. *(FR-10, FR-11)*
- [x] **T007 — REST:** `GET/POST /api/workspaces/{selector}/mcp`,
  `DELETE .../mcp/{name}`, `POST .../mcp/{name}/login` — thin concierge calls. *(FR-14)*
- [x] **T008 — Docs:** update `CLAUDE.md` API table + workspace layout with the new routes and
  the two new workspace files.
- [x] **T009 — Tests:** `tests/test_mcp_servers_api.py` — add/list/remove round-trip + idempotent
  (AC-1); malformed name rejected (AC-2); `.mcp-auth/` ignored, `.mcp.json` tracked + committed
  (AC-3); `login_mcp_server` config_dir + command (AC-4); offline `run_stream` sets
  `CLAUDE_CONFIG_DIR` + `mcp__<name>__*` (AC-5); four capabilities blacklisted (AC-6); routes
  registered (AC-7). Run `uv run --extra dev pytest` green. *(AC-1..AC-7)*
- [x] **T010 — Spec amendment (2026-09-19):** FR-10 gated on a registered server; FR-15 (restore
  `CLAUDE_CONFIG_DIR` after a run); FR-16 (actionable auth failure); AC-9..AC-11; D6; R2 finding.
- [x] **T011 — Config dir scoping:** `config.agent_config_dir`; `agent.run_stream` relocates only
  when a server is registered and restores the process-start value in `finally`. *(FR-10, FR-15)*
- [x] **T012 — Auth failure reason:** `agent.describe_runtime_error` maps `AssistantMessage.error`
  to an actionable `AgentUnavailable` in `run_stream` and `activity_ingest`. *(FR-16, P14)*
- [x] **T013 — Tests:** AC-9 (no relocation without servers), AC-10 (restored after run/error),
  AC-11 (auth failure message) in `tests/test_mcp_servers_api.py`; spec 002 AC-14 in
  `tests/test_chat_api.py`. *(AC-9..AC-11, 002 AC-14)*
