# Feature Specification: Expose the capability layer to the agent as MCP tools

**Feature ID:** `006-mcp-capability-tools`
**Status:** Draft
**Created:** 2026-08-16 · **Last Updated:** 2026-08-22

> **Superseded in part by [[007-knowledge-activities]] (2026-08-22).** The `ingest` MCP tool
> (originally FR-4/AC-1/AC-5/Scenario-3/D1 below) is **removed**: ingest is no longer a narrow
> `{title,content,provenance}` direct-execute tool but an internal **workflow** built on an
> activity (feature 007). All other parity tools in this feature are unchanged. Where the text
> below still lists `ingest` as a registered tool, read it as removed per feature 007 FR-12.

> Describes **what** and **why**. Gives the chat agent (Claude Agent SDK runtime) an
> in-process MCP tool for **every** capability-layer function — not just the original
> `query` / `spec_read` / `plan` trio — so the agent can answer and act through the same
> sanctioned capabilities the REST surface uses (P9 parity). Two capabilities are held back:
> **chat** (`ask`/`ask_stream`) is *structurally* never exposed (an agent calling the chat
> surface would recurse), and a **config-driven blacklist** the operator maintains removes
> anything else (default: `chat`, `upload`, `create_workspace`). Primary spec references:
> [[13-api]], [[12-assistant]], [[14-chat]], [[09-planning]], [[03-workspace]]. Builds on
> features [[002-assistant-chat]] (chat surface + agent runtime) and [[005-skill-import]]
> (workspace-scoped agent tool set); resolves the 005 chat parity gap for skill listing.

## Summary

Today the agent reaches the model with only three MCP tools — `query`, `spec_read`, `plan`
(`app/agent.py:_build_server`). Every other capability (`list_workspaces`,
`get_workspace_info`, `lint`, `wiki_tree`, `list_conversations`, `get_conversation`,
`list_available_skills`, `list_installed_skills`, `ingest`, `import_skill`, …) is reachable
over REST but **invisible to the agent**. This breaks capability parity in practice: e.g. a
chat request "list the skills I can install" cannot be answered because the catalog capability
(`list_available_skills`, spec 005 FR-2) is not a tool the agent can call — it falls through to
the knowledge `query` and returns nothing useful.

This feature makes the agent's MCP surface a **1:1 mirror of the capability layer**, minus a
governed exclusion set. Every capability function becomes an MCP tool **bound to the agent's
active workspace** (the agent cannot target another workspace — it stays sandboxed, spec 005
FR-9). `ingest` and `import_skill` execute **directly** when the agent calls them (consistent
with the autonomous-within-workspace execution model, spec 005 D1). The chat surface is never
exposed; `upload` and `create_workspace` are excluded by the default blacklist. REST is
unchanged — the blacklist governs only the **agent** MCP surface, so machine REST callers keep
full access.

## Goals

- Give the agent an MCP tool for **every** capability-layer function, so anything the REST
  surface can do, the agent can do (P9 parity), **except** the governed exclusions below.
- **Sandbox** every agent tool to the run's **active workspace**: the workspace/selector
  argument is injected from the run context; the agent cannot address another workspace
  (spec 005 FR-9).
- Let the agent **execute** the sanctioned mutating capabilities (`ingest`, `import_skill`)
  directly, matching the autonomous-within-workspace model (spec 005 D1).
- Make exclusions **operator-controlled via configuration** (a blacklist the operator updates
  without code changes), with safe defaults.
- **Prevent recursion:** the chat surface (`ask`/`ask_stream`) is never an agent tool.
- Resolve the [[005-skill-import]] chat gap: "what skills can I install / are installed?"
  now reaches `list_available_skills` / `list_installed_skills` through the agent.

## Non-Goals

- No change to the **REST** surface, its routes, or its shapes — parity is additive on the
  agent side only.
- No new capabilities — this exposes the **existing** capability functions; it does not author
  new behaviour.
- No plan-first gating change: chat-level plan-first for consequential *requests* stays as in
  [[002-assistant-chat]]/[[005-skill-import]]. This feature is about which *tools the agent may
  call* once it is already running a turn; the agent's mutating tools execute directly (D1).
- No per-tool fine-grained permissioning beyond the allow/deny blacklist (future work).
- No exposure of `upload` / `deposit_raw` to the agent — that is the **human** channel into
  `vault/raw/` and would defeat the P2 raw-guard (see Resolved Decisions D2).

## User Scenarios

- **Scenario 1 — List available skills from chat:** As an operator I ask "what skills can I
  install?"; the agent calls the catalog tool and lists the library's skills with descriptions
  and installed flags. *(Resolves the 005 gap.)*
- **Scenario 2 — Inspect the workspace from chat:** As an operator I ask "lint my workspace"
  or "what's in my wiki?"; the agent calls `lint` / `wiki_tree` and reports, all scoped to my
  active workspace.
- **Scenario 3 — Ingest via the agent:** ~~As an operator I ask the agent to record a note; it
  calls the `ingest` tool…~~ **Superseded by [[007-knowledge-activities]]:** there is no narrow
  `ingest` tool; ingest is an internal workflow over the `second-brain-ingest` activity.
- **Scenario 4 — Sandbox holds:** As an operator, even if the agent tries to name a *different*
  workspace in a tool call, the call still targets my active workspace; the agent cannot read
  or mutate another workspace.
- **Scenario 5 — Operator updates the blacklist:** As an operator I add a capability name to
  `LEADER_MCP_TOOL_BLACKLIST`; on the next turn that tool is no longer offered to the agent —
  no code change or redeploy of app code required.
- **Scenario 6 — No recursion:** As an operator, there is never a chat/`ask` tool for the
  agent to call, so the agent cannot invoke the chat surface from within a turn, even if the
  blacklist is emptied.

## Functional Requirements

Numbered, testable, unambiguous.

### Configurable exclusion

- **FR-1:** The system MUST resolve an **MCP tool blacklist** from configuration — env
  `LEADER_MCP_TOOL_BLACKLIST`, a comma-separated list of capability tool names — with a
  sensible **default of `{chat, upload, create_workspace}`**. Parsing MUST be tolerant of
  whitespace and empty entries and MUST NOT hardcode any absolute path.
- **FR-2:** A capability whose tool name is in the blacklist MUST NOT be registered as an agent
  MCP tool and MUST NOT appear in the agent's `allowed_tools`.

### Full capability tool surface (parity)

- **FR-3:** The agent's in-process MCP server MUST register a tool for **every** capability-layer
  function, **except** (a) the chat orchestration (`ask`/`ask_stream`), which MUST be
  *structurally* excluded (never registered, regardless of the blacklist, to prevent
  recursion), and (b) any tool named in the blacklist (FR-2). The registered read tools MUST
  include: `query`, `spec_read`, `plan`, `list_workspaces`, `get_workspace_info`, `lint`,
  `wiki_tree`, `list_conversations`, `get_conversation`, `list_available_skills`,
  `list_installed_skills`.
- **FR-4:** The registered **mutating** tools MUST include `import_skill`, and it MUST **execute
  directly** when the agent calls it (create the reference-link, update as applicable, and
  git-commit), consistent with the autonomous-within-workspace model (spec 005 D1).
  `create_workspace` and `upload` MUST NOT be registered (default blacklist, FR-1; and see D2 for
  `upload`). **`ingest` is NO LONGER a registered tool** — superseded by
  [[007-knowledge-activities]] FR-12; ingest is now a workflow, not a narrow MCP tool.
- **FR-5:** The `query` tool MUST preserve its citation-surfacing behaviour (citations returned
  by the capability are surfaced to the chat reply, as in feature 002).
- **FR-5a:** The server MAY also register **turn-local** tools that reach no workspace and whose
  result is consumed by the running turn rather than persisted by the tool itself. `name_conversation`
  ([[012-conversation-naming]] FR-4) is one: it records the title/tags proposal for the conversation
  currently being answered. Such a tool MUST still declare an effect tier in `capabilities.EFFECTS`
  (`auto`), because the risk layer reads that table for every tool call ([[011-maker-checker-approval]]
  FR-5) and an undeclared capability defaults to the `reversible` tier.

### Workspace sandbox

- **FR-6:** Every registered capability tool MUST be **bound to the agent run's active
  workspace**: the workspace/selector argument passed to the capability is injected from the
  run context, NOT from tool arguments. A workspace value supplied in tool arguments MUST be
  ignored. This keeps the agent sandboxed to one workspace (spec 005 FR-9).

### Parity & governance

- **FR-7:** The **REST** surface MUST be unaffected: no route or shape is removed or changed,
  and the blacklist MUST NOT apply to REST (machine callers keep full capability access). The
  blacklist governs only the **agent** MCP surface.
- **FR-8:** The agent's `allowed_tools` list MUST be derived from the **same** selected tool set
  (native tools + the non-excluded capability tools), so an excluded tool is neither declared
  nor permitted.

## Key Entities & Concepts

- **Capability tool** — an in-process MCP tool wrapping one capability-layer function, with a
  handler that injects the active workspace and serialises the capability's result to tool text
  (FR-3/FR-6).
- **MCP tool blacklist** — the operator-maintained set of tool names withheld from the agent
  (FR-1/FR-2), default `{chat, upload, create_workspace}`.
- **Structural exclusion** — `ask`/`ask_stream` is never a tool, independent of the blacklist,
  to prevent the agent from re-entering the chat surface (FR-3, recursion guard).
- **Workspace binding** — the mechanism that pins every tool to the run's active workspace
  (FR-6), the agent's sandbox boundary.

## Constraints & Assumptions

- **Constitution:** P9 (REST↔chat/agent parity — this feature closes the practical gap), P8
  (chat-level plan-first for consequential *requests* is unchanged; the agent's direct tool
  execution is the already-ratified autonomous model of 005 D1), P2 (`vault/raw/` immutability —
  preserved: `upload`/`deposit_raw` is not exposed and the FR-10 raw-guard from 005 still covers
  the native write tools), P10 (git ledger; mutating tools commit), P13 (workspace-scoped — the
  sandbox binding, FR-6).
- **Builds on** feature 002 (agent runtime, in-process MCP server, citation surfacing) and
  feature 005 (workspace-scoped tool set, raw-guard hook, skill capabilities).
- **SDK assumption:** in-process MCP tools are created with `create_sdk_mcp_server` + `@tool`
  (as in feature 002); `allowed_tools` must name each `mcp__leader__<tool>` for the tool to be
  callable.
- **Assumption:** single-operator, local, trusted machine (as in 005). Direct execution of
  `ingest`/`import_skill` by the agent is acceptable because the agent is workspace-sandboxed
  and the per-workspace git repo is the backstop.

## Acceptance Criteria

- [ ] **AC-1:** With the default configuration, the agent's MCP server registers exactly the
  parity tool set — `query`, `spec_read`, `plan`, `list_workspaces`, `get_workspace_info`,
  `lint`, `wiki_tree`, `list_conversations`, `get_conversation`, `list_available_skills`,
  `list_installed_skills`, `import_skill` — and **not** `chat`/`ask`, `upload`,
  `create_workspace`, or `ingest` (ingest removed per [[007-knowledge-activities]] FR-12).
  (FR-1, FR-2, FR-3, FR-4)
- [ ] **AC-2:** `chat`/`ask` is never registered even when the blacklist is emptied
  (`LEADER_MCP_TOOL_BLACKLIST=""`). (FR-3 structural exclusion)
- [ ] **AC-3:** Adding a name to `LEADER_MCP_TOOL_BLACKLIST` removes exactly that tool from both
  the registered set and `allowed_tools`; removing the default value for `upload`/
  `create_workspace` would re-admit them (proving the default is config, not hardcode). (FR-1,
  FR-2, FR-8)
- [ ] **AC-4:** Every registered tool is workspace-bound: invoking a tool handler with a
  *different* workspace in its arguments still operates on the run's active workspace. (FR-6)
- [ ] **AC-5:** ~~The `ingest` tool handler…~~ **Superseded by [[007-knowledge-activities]]** —
  no `ingest` tool. The `import_skill` tool handler creates the reference-link and commit in the
  active workspace. (FR-4)
- [ ] **AC-6:** A chat turn asking "what skills can I install?" reaches `list_available_skills`
  through the agent and returns the catalog. (FR-3; resolves 005 gap.) *(Exercised by the opt-in
  live-agent test; offline tests cover the registry, handlers, blacklist, and binding.)*
- [ ] **AC-7:** The REST surface is unchanged — all existing routes still respond and the
  blacklist has no effect on them. (FR-7)

## Resolved Decisions

- **D1 — Direct execution for `import_skill`:** the agent calls this tool and it executes
  immediately (no per-tool approval), matching the autonomous-within-workspace execution model
  ratified in spec 005 D1. Chat-level plan-first for consequential *requests* is unchanged.
  *(Originally covered `ingest` too; `ingest` is removed per [[007-knowledge-activities]] D7/FR-12.)*
- **D2 — `upload`/`deposit_raw` stays human-only:** exposing the upload capability to the agent
  would let it write `vault/raw/` (that capability deliberately bypasses `guard_write_path` as
  the sanctioned human channel), defeating P2 and the 005 FR-10 raw-guard. It is therefore in
  the **default blacklist**, controllable by the operator. *(User decision — enforce via the
  config blacklist the operator maintains.)*
- **D3 — `create_workspace` excluded:** creating a *new sibling* workspace is broader than the
  agent's "scoped to the active workspace" boundary (spec 005 FR-9); it is in the default
  blacklist. Workspace creation remains a chat plan-first / REST action. *(User decision.)*
- **D4 — Chat is a structural exclusion, not merely blacklisted:** `ask`/`ask_stream` is never
  registered as a tool regardless of blacklist contents, because an agent calling the chat
  surface would recurse. The blacklist still lists `chat` by default for operator visibility.
  *(User decision + design.)*
- **D5 — Blacklist, not allowlist:** exposure is opt-out (expose all, subtract the blacklist)
  rather than opt-in, so new capabilities are automatically available to the agent and the
  operator narrows as needed. *(Design decision.)*
- **D6 — Workspace binding by injection:** tool schemas omit a workspace argument; the handler
  closes over the run's active selector. This makes the sandbox unbypassable from tool
  arguments (FR-6). *(Design decision.)*

## Review Checklist

- [ ] No implementation details (how) leaked beyond what parity/governance require.
- [ ] Every requirement is testable.
- [ ] Scenarios cover the golden path and key edge cases (sandbox, recursion, blacklist).
- [ ] Complies with `memory/constitution.md` (P2 preserved via D2; P9 advanced).
- [ ] Parity preserved and REST left unchanged (FR-7).
