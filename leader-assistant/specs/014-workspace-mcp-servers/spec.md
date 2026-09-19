# Feature Specification: Per-workspace MCP servers with captured OAuth login

**Feature ID:** `014-workspace-mcp-servers`
**Status:** Draft
**Created:** 2026-09-12 · **Last Updated:** 2026-09-12

> Describes **what** and **why**. Lets an operator attach an **external** MCP server (e.g.
> Atlassian at `https://mcp.atlassian.com/v1/mcp`) to a **single workspace**, and log in to
> that server **once** so the login is **captured inside the workspace** and reused by later
> agent runs. Primary spec references: [[15-integrations]] (the external-integration
> boundary this realises), [[03-workspace]] (workspace layout + git ledger), [[13-api]] (REST
> parity), [[006-mcp-capability-tools]] (the agent MCP surface + operator blacklist),
> [[011-maker-checker-approval]] (effect-based gating). Builds on features
> [[002-assistant-chat]] (agent runtime) and [[006-mcp-capability-tools]] (blacklist).

## Summary

Today the agent runtime (`app/agent.py:run_stream`) loads exactly **one** MCP server: the
in-process `leader` capability server. A workspace cannot declare an external MCP server, and
there is nowhere to hold the OAuth login such a server requires. This feature adds both:

1. **Per-workspace registration** in a standard `<workspace>/.mcp.json` — the same schema the
   `claude` CLI already discovers, because the agent runs with `setting_sources=["project"]`
   and `cwd=<workspace>` (spec 006). A capability trio (`list`/`add`/`remove_mcp_server`)
   writes it, so the surface is reachable over REST, chat, and UI (P9).
2. **Per-workspace login capture** by pointing the CLI's config+credential directory at a
   workspace-local path via the `CLAUDE_CONFIG_DIR` environment variable. The operator logs in
   once (OAuth browser flow); the token lands under `<workspace>/.mcp-auth/`, and every later
   agent run for that workspace sets the same `CLAUDE_CONFIG_DIR` so the captured token is
   reused without a second login.

Managing external integrations and their credentials is an **operator** action, not something
the agent does to itself: the four new capabilities are added to the default agent MCP
**blacklist** (spec 006 FR-1), alongside `create_workspace`.

## Why the login is captured this way

The Claude Agent SDK cannot itself run an interactive browser OAuth flow; it can only reuse the
`claude` CLI's own credential store or send a pre-provisioned header token. Reusing the CLI's
store (rather than reimplementing OAuth) is the least-code path that gives a real "log in once"
experience **and** the CLI's own token handling. Relocating that store per workspace with
`CLAUDE_CONFIG_DIR` is what makes the captured login **workspace-scoped and portable with the
workspace** rather than a single global login shared across every workspace.

## Goals

- Let an operator **add/list/remove** external MCP servers on a **single workspace**, stored in
  `<workspace>/.mcp.json` (no secrets in that file — just name/url/transport).
- Let an operator **log in once** to a server that requires OAuth and have that login **captured
  inside the workspace** (`<workspace>/.mcp-auth/`), reused by later agent runs with no second
  login until the token actually expires.
- Make the registered external servers' tools **available to the agent** for that workspace
  (`allowed_tools` includes `mcp__<name>__*`), still under the existing PreToolUse risk gate.
- Keep credential material **out of git** (`.mcp-auth/` git-ignored) while keeping the
  **registration** in git (`.mcp.json` tracked + committed).
- Keep integration/credential management **operator-only** (default agent blacklist), and
  reachable identically over REST, chat, and UI (P9).

## Non-Goals

- **No** reimplementation of an OAuth2 client, discovery, or refresh in this app. Login uses the
  `claude` CLI's own flow and store.
- **No** headless/unattended first login — a human completes the browser round-trip once
  (the SDK/CLI offers no non-interactive single-server auth). The login capability *drives and
  reports* that flow; it does not eliminate the browser step.
- **No** continuous synchronization with the external system (that boundary rule is
  [[15-integrations]] §2, unchanged).
- **No** new capability for the agent to add/remove servers or manage credentials — those are
  operator-only (default blacklist).
- **No** per-server fine-grained tool permissioning beyond `mcp__<name>__*` + the existing
  PreToolUse risk gate.

## User Scenarios

- **Scenario 1 — Add a server:** As an operator I `POST /api/workspaces/demo/mcp` with
  `{name: "atlassian", url: "https://mcp.atlassian.com/v1/mcp"}`; `<demo>/.mcp.json` now
  registers the server and the change is committed.
- **Scenario 2 — Log in once:** I `POST /api/workspaces/demo/mcp/atlassian/login`; the OAuth
  browser flow runs with `CLAUDE_CONFIG_DIR=<demo>/.mcp-auth`, I authorise once, and the token is
  captured under `<demo>/.mcp-auth/`.
- **Scenario 3 — Reuse without re-login:** On a later chat turn in `demo`, the agent calls an
  `mcp__atlassian__*` tool and it works — the run set the same `CLAUDE_CONFIG_DIR`, so the
  captured token is reused with no second login. Restarting the server does not lose the login.
- **Scenario 4 — List / auth status:** I `GET /api/workspaces/demo/mcp`; I see each registered
  server with its url, transport, and an `authenticated` flag reflecting whether a token is
  captured for it.
- **Scenario 5 — Remove a server:** I `DELETE /api/workspaces/demo/mcp/atlassian`; the entry
  leaves `.mcp.json` (git-recoverable) and the agent no longer offers its tools.
- **Scenario 6 — Isolation:** A server + login on workspace `demo` is invisible to workspace
  `other`; each workspace has its own `.mcp.json` and its own `.mcp-auth/` (P13).
- **Scenario 7 — Operator-only:** The agent has no tool to add, remove, or log in to servers —
  those capabilities are in the default blacklist, so the agent cannot manage integrations or
  credentials on its own.

## Functional Requirements

Numbered, testable, unambiguous.

### Registration

- **FR-1:** The system MUST store a workspace's external MCP servers in `<workspace>/.mcp.json`
  using the standard `{"mcpServers": {"<name>": {"type": "http"|"sse", "url": "..."}}}` schema
  the `claude` CLI reads.
- **FR-2:** `add_mcp_server(selector, name, url, transport="http")` MUST create or merge the
  named server into `<workspace>/.mcp.json`, validate `name` (`[A-Za-z0-9_-]+`) and reject a
  malformed name, default `transport` to `http`, and be idempotent (re-adding the same name
  updates in place, no duplicate).
- **FR-3:** `list_mcp_servers(selector)` MUST return every registered server for the workspace
  with its `name`, `url`, `transport`, and an `authenticated` flag (FR-9).
- **FR-4:** `remove_mcp_server(selector, name)` MUST remove the named server from `.mcp.json`
  (a no-op error if absent) and leave the remaining registrations intact.
- **FR-5:** `.mcp.json` MUST be **tracked in git**; a workspace-mutating registration
  (`add`/`remove`) MUST be committed to the workspace's own repo (P10), so it is revertible.

### Login capture

- **FR-6:** Each workspace MUST have a dedicated CLI config+credential directory at
  `<workspace>/.mcp-auth/`, used as `CLAUDE_CONFIG_DIR` for both the login flow and later agent
  runs, so a captured login is workspace-scoped.
- **FR-7:** `<workspace>/.mcp-auth/` MUST be **git-ignored** (it holds credential material); it
  MUST NOT be committed.
- **FR-8:** `login_mcp_server(selector, name)` MUST run/drive the CLI OAuth flow with
  `CLAUDE_CONFIG_DIR=<workspace>/.mcp-auth`, and MUST return the exact `config_dir` used and a
  ready-to-run fallback command an operator can execute manually (since the flow is interactive
  and cannot be completed unattended).
- **FR-9:** `authenticated` MUST be a best-effort reflection of whether a token has been captured
  for the server under `<workspace>/.mcp-auth/`; when it cannot be determined it MUST default to
  `false` (never a false positive).

### Agent runtime wiring

- **FR-10 (amended 2026-09-19):** Before invoking the agent for a workspace **that has at least one
  server registered** in its `.mcp.json`, the runtime MUST set `CLAUDE_CONFIG_DIR` to that
  workspace's `.mcp-auth/` so captured tokens are found, and MUST add `mcp__<name>__*` to
  `allowed_tools` for every registered server. For a workspace with **no** registered server the
  runtime MUST NOT relocate `CLAUDE_CONFIG_DIR`: the CLI runs with the operator's own config (the
  value the process started with, or the CLI default), so the operator's existing `claude` login
  keeps working. *(A relocated config dir does not see the default login — verified, see R2.)*
- **FR-11:** External MCP tool calls MUST remain subject to the existing PreToolUse risk gate
  (spec 011) — this feature adds a tool surface, it does not bypass gating.
- **FR-15 (no leak):** A relocation made for one agent run (FR-10) MUST be undone when that run
  ends (normally, on error, or on client disconnect): `CLAUDE_CONFIG_DIR` is restored to the value
  the process started with (unset if it was unset). Other SDK call sites that do not relocate
  (ingest activity, judge) MUST therefore never inherit a workspace's `.mcp-auth/`.
- **FR-16 (actionable auth failure):** When the CLI reports a runtime error on an assistant
  message (e.g. `authentication_failed` → "Not logged in · Please run /login"), the runtime MUST
  raise `AgentUnavailable` carrying that error kind, the CLI's text, the effective
  `CLAUDE_CONFIG_DIR` (or "default"), and — for `authentication_failed` — the remedy: run
  `claude /login` with that config dir, or provide `CLAUDE_CODE_OAUTH_TOKEN` (from
  `claude setup-token`) or `ANTHROPIC_API_KEY` in the server environment. It MUST NOT surface the
  SDK's opaque "Claude Code returned an error result" in place of that reason (Constitution P14).

### Governance & parity

- **FR-12:** `add_mcp_server`, `remove_mcp_server`, `login_mcp_server`, and `list_mcp_servers`
  MUST be in the **default agent MCP blacklist** (spec 006 FR-1), so the agent cannot manage
  external servers or credentials; the operator MAY re-admit them via configuration.
- **FR-13:** Every new capability MUST declare an effect tier in `capabilities.EFFECTS`
  (spec 009/011 FR-5): `list_mcp_servers`→`auto`, `add_mcp_server`→`reversible`,
  `remove_mcp_server`→`reversible` (both are git-recoverable `.mcp.json` edits — committed to the
  workspace repo so one revert undoes them), `login_mcp_server`→`auto` (operator-initiated; the
  credential lands in git-ignored `.mcp-auth/`). The privilege concern that would otherwise push
  `add` to `approval` is covered structurally instead: these capabilities are operator-only
  (FR-12), a registered server is inert until a separate deliberate login (FR-8), and every
  external tool call still faces the PreToolUse risk gate (FR-11).
- **FR-14:** The four capabilities MUST be reachable over REST at
  `GET/POST /api/workspaces/{selector}/mcp`, `DELETE /api/workspaces/{selector}/mcp/{name}`,
  `POST /api/workspaces/{selector}/mcp/{name}/login`, each a thin call through the concierge
  (spec 011 FR-23), matching the existing route pattern.

## Key Entities & Concepts

- **`.mcp.json`** — per-workspace registration file (tracked in git), standard CLI schema.
- **`.mcp-auth/`** — per-workspace `CLAUDE_CONFIG_DIR` (git-ignored) holding captured OAuth
  tokens/config.
- **`McpServerInfo` / `McpServerList` / `McpLoginInfo`** — the wire contracts (spec 13-api).
- **Operator-only integration management** — the four capabilities in the default blacklist.

## Constraints & Assumptions

- **Constitution:** P9 (REST↔chat/UI parity — the capability trio), P10 (`.mcp.json` in the git
  ledger; `.mcp-auth/` deliberately outside it as credential material), P13 (workspace-scoped —
  one `.mcp.json` and one `.mcp-auth/` per workspace), P8 (external MCP tool calls stay under the
  maker–checker gate, FR-11).
- **SDK/CLI facts (confirmed):** `setting_sources=["project"]` + `cwd` discovers
  `<workspace>/.mcp.json`; `CLAUDE_CONFIG_DIR` relocates the CLI's config+credential dir and the
  SDK subprocess inherits `os.environ`; `ClaudeAgentOptions` has no `env` field, so the runtime
  sets `os.environ["CLAUDE_CONFIG_DIR"]` for the run.
- **SDK/CLI fact (verified 2026-09-19, macOS, CLI 2.1.270 / SDK 0.2.139):** a CLI started with a
  fresh `CLAUDE_CONFIG_DIR` does **not** see the operator's default login and answers
  `Not logged in · Please run /login` (`AssistantMessage.error == "authentication_failed"`); the
  SDK then raises the opaque `Claude Code returned an error result: success`. Env credentials
  (`CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_API_KEY`) are honoured regardless of the config dir.
- **Assumption:** single-operator, local, trusted machine (as in feature 005/006). One agent
  run at a time per process for a given workspace — see Risk R1.

## Acceptance Criteria

- [x] **AC-1:** `add_mcp_server` writes/merges `<workspace>/.mcp.json` in the standard schema and
  is idempotent; `list_mcp_servers` reads it back; `remove_mcp_server` removes exactly the named
  entry. (FR-1..FR-4)
- [x] **AC-2:** A malformed server name is rejected with no write. (FR-2)
- [x] **AC-3:** `.mcp-auth/` is git-ignored and `.mcp.json` is tracked; an add/remove is
  committed to the workspace repo. (FR-5, FR-7)
- [x] **AC-4:** `login_mcp_server` returns `config_dir == <workspace>/.mcp-auth` and a runnable
  fallback command; the browser round-trip itself is a documented manual step, not asserted.
  (FR-8)
- [x] **AC-5:** For a workspace with a registered server, the agent runtime sets
  `CLAUDE_CONFIG_DIR` to that workspace's `.mcp-auth/` during the run and includes
  `mcp__<name>__*` in `allowed_tools`. (FR-10) *(Exercised offline by asserting the assembled options.)*
- [x] **AC-9:** For a workspace with **no** registered server, the agent run leaves
  `CLAUDE_CONFIG_DIR` at the process's original value (unset stays unset). (FR-10)
- [x] **AC-10:** After a run for a workspace with a registered server ends — normally or with an
  error — `CLAUDE_CONFIG_DIR` is back to the process's original value. (FR-15)
- [x] **AC-11:** A CLI `authentication_failed` assistant message makes `run_stream` raise
  `AgentUnavailable` whose message names the CLI text, the config dir and the login/token remedy,
  not "Claude Code returned an error result". (FR-16)
- [x] **AC-6:** With the default configuration, none of the four MCP-management capabilities are
  registered as agent tools. (FR-12)
- [x] **AC-7:** All four routes exist and are thin concierge calls; the REST surface is otherwise
  unchanged. (FR-14)
- [ ] **AC-8 (manual/live):** After one login on workspace `demo`, an agent turn in `demo`
  invokes an `mcp__atlassian__*` tool without a second login, and it still works after a server
  restart. Empirically confirm the token is captured under `<demo>/.mcp-auth/`. (FR-6, FR-10;
  see Risk R2)

## Resolved Decisions

- **D1 — Reuse the CLI credential store via `CLAUDE_CONFIG_DIR`, not a hand-rolled OAuth client.**
  Least code, real "login once", and the CLI owns token handling. The per-workspace config dir is
  what makes the login workspace-scoped. *(User decision — chosen over app-driven OAuth and a
  static PAT header.)*
- **D2 — Registration in `<workspace>/.mcp.json` via a capability trio.** Uses the schema the CLI
  already reads (no duplicate `mcp_servers` wiring needed) and keeps REST/chat/UI parity (P9).
  *(User decision.)*
- **D3 — Integration/credential management is operator-only.** The four capabilities are in the
  default agent blacklist alongside `create_workspace`; managing external tool surfaces and
  logins is broader than the agent's within-workspace remit. *(Design, consistent with 006 D2/D3.)*
- **D4 — `.mcp.json` tracked, `.mcp-auth/` ignored.** Registration is knowledge worth versioning;
  credentials are not, and must never enter git. *(Design, P10.)*
- **D5 — `add`/`remove` are `reversible`, `login`/`list` are `auto`.** Both `add_mcp_server`
  and `remove_mcp_server` edit `.mcp.json` and commit it to the workspace repo, so a single
  `git revert` undoes either — the definition of the `reversible` tier. The privilege concern
  that would otherwise push `add` to `approval` (like `import_skill`) is covered structurally
  instead: the four capabilities are operator-only (D3/FR-12), a registered server is inert
  until a separate, deliberate `login` (FR-8), and every external tool call still faces the
  PreToolUse risk gate (FR-11). This also keeps `add` on the frictionless auto-run path rather
  than the REST approval-resume path, which re-dispatches through the chat executor and cannot
  carry the extra `url` argument. `list`/`login` are `auto` (read-only / credential write lands
  in git-ignored `.mcp-auth/`, nothing in the ledger to undo). *(Design, spec 011 FR-37.)*

- **D6 — Relocate the config dir only when it buys something (2026-09-19).** Unconditionally
  pointing every run at `.mcp-auth/` logged the agent out of every workspace without MCP servers
  (observed on `cost-management`: chat silently degraded to the keyword fallback). Relocation is
  now gated on a registered server (FR-10), scoped to the run (FR-15), and an auth failure names
  its remedy (FR-16). A workspace with servers still needs Anthropic auth in its `.mcp-auth/` —
  either an interactive `/login` there (the `login_mcp_server` command covers it) or an env token.
  *(User decision — chosen over a per-workspace `/login` without code change.)*

## Known Risks & Caveats

- **R1 — Process-global `CLAUDE_CONFIG_DIR`.** `ClaudeAgentOptions` has no per-invocation `env`,
  so the runtime sets `os.environ["CLAUDE_CONFIG_DIR"]` for the run. Concurrent agent runs across
  *different* workspaces in one process could race on this global. Acceptable for the
  single-operator local model; noted so a future multi-tenant build isolates it (e.g. subprocess
  env). Set it immediately before `query()`.
- **R2 — macOS may store the token in the Keychain, not `.mcp-auth/`.** The login step MUST be
  verified empirically (AC-8). If the CLI uses the Keychain on this platform, the token is not
  workspace-portable via the config dir; record the finding here after verification and, if
  needed, document forcing file-based storage. **Finding (2026-09-19):** the operator's default
  Anthropic login is not visible under a relocated config dir (see Constraints); mitigated by
  D6/FR-10/FR-16. MCP OAuth token portability (AC-8) is still unverified.
- **R3 — OAuth token refresh is not reliably automatic.** A captured login may eventually expire
  and require a repeat `login_mcp_server`. This is why `authenticated` (FR-9) is surfaced and
  re-login is a one-command repeat.

## Review Checklist

- [ ] No implementation detail leaked beyond what parity/governance require.
- [ ] Every requirement is testable.
- [ ] Scenarios cover the golden path and edge cases (isolation, operator-only, removal).
- [ ] Complies with `memory/constitution.md` (P9/P10/P13/P8).
- [ ] Credentials never enter git (FR-7/D4).
