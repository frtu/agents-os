# Implementation Plan: Per-workspace MCP servers with captured OAuth login (014)

**Feature ID:** `014-workspace-mcp-servers` · **Status:** Draft · **Created:** 2026-09-12

Companion to [`spec.md`](spec.md). Records the **decided** design. Cite requirements as
`spec 014 FR-N` in code comments.

## Context

`app/agent.py:run_stream` loads exactly one MCP server (the in-process `leader` capability
server) and derives `allowed_tools` from the capability registry (spec 006). It already runs
with `setting_sources=["project"]` and `cwd=<workspace>`, so the `claude` CLI already
discovers a standard `<workspace>/.mcp.json`. There is no place to hold the OAuth login an
external server requires. This feature adds per-workspace registration (`.mcp.json`) and
per-workspace login capture (`.mcp-auth/` as `CLAUDE_CONFIG_DIR`).

## Design

```
Workspaces/<ws>/
  .mcp.json      # external server registrations — tracked in git (url only, no secrets)
  .mcp-auth/     # per-workspace CLAUDE_CONFIG_DIR — git-ignored (holds the OAuth token)
```

- **Registration** lives in `<ws>/.mcp.json` (the schema the CLI already reads). A capability
  trio (`list`/`add`/`remove_mcp_server`) writes it → REST/chat/UI parity (P9). These are
  operator actions: added to the default agent MCP blacklist (like `create_workspace`).
- **Login capture**: `login_mcp_server` sets `CLAUDE_CONFIG_DIR=<ws>/.mcp-auth` and launches
  the CLI OAuth flow for the named server. It reports the captured/auth status and the exact
  ready-to-run command as an operator fallback (the flow is interactive).
- **Run-time wiring**: before building `ClaudeAgentOptions`, `run_stream` (a) sets
  `os.environ["CLAUDE_CONFIG_DIR"]` to the workspace auth dir so captured tokens are found,
  and (b) adds `mcp__<name>__*` for each registered external server to `allowed_tools`. The
  servers themselves load via the existing `setting_sources=["project"]` path — no duplicate
  `mcp_servers` entry needed.

## Code changes

### `app/config.py`
- `workspace_mcp_config_path(workspace: Path) -> Path` → `<ws>/.mcp.json`.
- `workspace_mcp_auth_dir(workspace: Path) -> Path` → `<ws>/.mcp-auth`.
- `workspace_mcp_servers(workspace: Path) -> dict` — read/parse `.mcp.json` tolerant of a
  missing/corrupt file (return `{}`), mirroring `_read_settings`. Returns the `mcpServers` map.
- Add `list_mcp_servers`, `add_mcp_server`, `remove_mcp_server`, `login_mcp_server` to
  `DEFAULT_MCP_TOOL_BLACKLIST` (config.py:52). *(FR-12)*

### `app/models.py`
- `McpServerInfo {name, url, transport, authenticated}`.
- `McpServerList {workspace, servers: list[McpServerInfo]}`.
- `McpLoginInfo {workspace, server, config_dir, command, authenticated}`.

### `app/capabilities.py`
- `list_mcp_servers(selector) -> McpServerList` — read `config.workspace_mcp_servers`, map to
  `McpServerInfo`, compute `authenticated` best-effort from `.mcp-auth/`. *(FR-3, FR-9)*
- `add_mcp_server(selector, name, url, transport="http") -> McpServerInfo` — validate name
  (`_safe_name`), merge into `.mcp.json`, then `_record_turn_effects` (log + commit). *(FR-1, FR-2, FR-5)*
- `remove_mcp_server(selector, name) -> McpServerInfo` — drop the entry, commit. *(FR-4, FR-5)*
- `login_mcp_server(selector, name) -> McpLoginInfo` — set `CLAUDE_CONFIG_DIR=<ws>/.mcp-auth`,
  drive the CLI OAuth flow, return `config_dir` + fallback command + `authenticated`. *(FR-8)*
- Register all four in `EFFECTS`: list→`auto`, add→`reversible`, remove→`reversible`,
  login→`auto`. *(FR-13, D5)* No chat resolvers — operator-only (blacklisted), so no agent path.
- `.mcp.json` writes go through `_record_turn_effects` (log + commit); `.mcp-auth/` is
  git-ignored, never committed.

### `app/vault.py` / `templates/_workspace_/.gitignore`
- Ensure the workspace `.gitignore` ignores `.mcp-auth/`. Add `.mcp-auth/` to the template
  `.gitignore` so new workspaces get it; `.mcp.json` stays tracked. *(FR-7)*

### `app/agent.py` (`run_stream`)
- Before building options: `os.environ["CLAUDE_CONFIG_DIR"] = str(config.workspace_mcp_auth_dir(workspace_path))`
  and extend `allowed_tools` with `mcp__<name>__*` for each server in
  `config.workspace_mcp_servers(workspace_path)`. *(FR-10)* External tools stay under the
  existing PreToolUse gate (FR-11) — no change to the hook.

### `app/api.py`
- `GET /api/workspaces/{selector}/mcp` → `list_mcp_servers`.
- `POST /api/workspaces/{selector}/mcp` `{name,url,transport?}` → `add_mcp_server` (via concierge).
- `DELETE /api/workspaces/{selector}/mcp/{name}` → `remove_mcp_server` (via concierge).
- `POST /api/workspaces/{selector}/mcp/{name}/login` → `login_mcp_server` (via concierge).
- Thin calls, matching the existing workspace-route pattern. *(FR-14)*

### `CLAUDE.md`
- Add the four routes to the API table; add `.mcp.json` + `.mcp-auth/` to the workspace layout.

## Tests (`tests/`, offline + deterministic)

New `tests/test_mcp_servers_api.py`:
- **AC-1:** add → list → remove round-trips `<ws>/.mcp.json` in the standard schema; add is
  idempotent (re-add updates in place). *(FR-1..FR-4)*
- **AC-2:** a malformed name is rejected with no write. *(FR-2)*
- **AC-3:** `.mcp-auth/` git-ignored, `.mcp.json` tracked; add/remove committed. *(FR-5, FR-7)*
- **AC-4:** `login_mcp_server` returns `config_dir == <ws>/.mcp-auth` and a runnable command;
  browser round-trip is a documented manual step, not asserted. *(FR-8)*
- **AC-5:** offline `run_stream` sets `CLAUDE_CONFIG_DIR` to the workspace `.mcp-auth/` and puts
  `mcp__<name>__*` in `allowed_tools` when a server is registered. *(FR-10)*
- **AC-6:** the four capabilities are in the default agent blacklist (not registered as tools).
  *(FR-12)*
- **AC-7:** all four routes are registered and thin. *(FR-14)*
- Link each test to its FR (`test_..._fr3`).

Run `uv run --extra dev pytest` green.

## Key risks

1. **`allowed_tools` must match the discovered servers** — derive `mcp__<name>__*` from the
   same `.mcp.json` the CLI reads so a registered server is always callable. *(FR-10)*
2. **Process-global `CLAUDE_CONFIG_DIR`** — set immediately before `query()`; acceptable for the
   single-operator local model (spec R1).
3. **macOS Keychain** — the token may land in the Keychain, not `.mcp-auth/`; verify empirically
   (AC-8 / spec R2) before claiming portability.
4. **Blacklist coverage** — all four names must be in `DEFAULT_MCP_TOOL_BLACKLIST` or the agent
   could manage integrations itself (spec R / FR-12).
