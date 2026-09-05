---
id: 202608152112-13
title: API
spec: 13-api
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [api, parity, capabilities]
traceability:
  readme: ["§17 API and Chat Parity", "§18 Assistant Architecture"]
  references: []
related:
  - "[[12-assistant]]"
  - "[[14-chat]]"
  - "[[09-planning]]"
  - "[[15-integrations]]"
Created: 2026-08-15
Last Updated: 2026-08-15
---

# API

Chat and API expose the **same** underlying capabilities. The API is the machine-facing surface over the shared capability layer.

## 1. Parity Model

```text
      Chat            API
        └──────┬───────┘
        Assistant capability layer
        ┌───────┼───────┐
   Knowledge  Planning  Execution
        └───────┼───────┘
           Specifications
```

- The API MUST NOT bypass the planning/risk/knowledge model.
- Any capability offered in Chat MUST be invocable via API, and vice versa.

## 2. Capability Surface (derived)

The API SHALL expose, at minimum, capabilities for:
- **Knowledge**: query the Vault with citations; inspect a concept/source/portal.
- **Ingestion**: register/notify a raw source; trigger/inspect ingestion.
- **Specification**: read specs; request a spec draft/update; transition lifecycle (review/approve).
- **Planning**: submit a work request → receive a plan; critique/approve a plan.
- **Operations**: run dreaming / lint on demand; read log.
- **Skills**: list available skills in the shared library; list a workspace's installed skills;
  import (reference-link) a skill into a workspace — see [[005-skill-import]]. Chat import is
  plan-first (P8); the REST import performs the install directly for machine callers.
- **Integration**: request an external PM action (user-initiated) — see [[15-integrations]].

Exact endpoint shapes are defined at implementation time; the constraint is capability parity, not a specific transport.

### 2.1 Agent MCP tool surface (parity for the chat agent) — see [[006-mcp-capability-tools]]

The chat agent reaches the capability layer through in-process **MCP tools**. To keep the agent
in genuine parity with REST, the agent's MCP server SHALL register a tool for **every**
capability-layer function, minus a governed exclusion set:

- **Structural exclusion:** the chat surface itself (`ask`/`ask_stream`) is **never** an agent
  tool — an agent calling chat would recurse.
- **Configurable blacklist:** an operator-maintained blacklist (`LEADER_MCP_TOOL_BLACKLIST`,
  default `{chat, upload, create_workspace}`) withholds further tools. `upload`/`deposit_raw`
  stays human-only so the agent cannot write `vault/raw/` (preserves P2 and the 005 raw-guard);
  `create_workspace` is withheld so the agent stays scoped to its active workspace.
- **Workspace sandbox:** every agent tool is **bound to the run's active workspace** — the
  workspace argument is injected from the run context and any workspace supplied in tool
  arguments is ignored (spec 005 FR-9).
- **Direct execution:** the sanctioned mutating tools (`ingest`, `import_skill`) execute directly
  when the agent calls them (autonomous-within-workspace, spec 005 D1); chat-level plan-first for
  consequential *requests* is unchanged.

The blacklist governs only the **agent** MCP surface; the REST surface is unaffected — machine
callers keep full capability access.

## 3. Governance Through the API

Requests that are consequential still flow through [[09-planning]] and [[10-risk-engine]]; the API returns plans/risk outcomes rather than silently executing.

### 3.1 Effect-based gating + trust mode ([[009-approval-optimization]])

"Consequential" means **an executable capability whose declared effect tier is `approval`** — not a
request that contains risky-sounding words. Concretely:

- `auto`/`reversible` capabilities execute on call; `reversible` ones commit to the workspace repo.
- An executable `approval`-tier action returns a **plan** naming capability/target/tier/undo path.
- A request mapping to no executable capability returns a normal answer, never a plan.

**Contract additions:**

- `ChatRequest.auto_approve: bool | null` — per-request standing consent. `true` runs an
  `approval`-tier action without prompting; `false` forces a prompt; omitted uses the persisted
  setting (009 FR-7/FR-9).
- `GET /api/settings` → `Settings {auto_approve, agent_model}` and `POST /api/settings`
  → `SettingsUpdate {auto_approve?}` — read/update the persisted operator settings, in parity with
  `GET`/`POST /api/models` (009 FR-8). Persisted in `LEADER_SETTINGS_PATH`.
- These two settings routes are **structurally excluded** from the agent MCP surface (§2.1): trust
  mode is standing consent only the operator grants, so the agent has no tool to read, set, or
  bypass it (009 FR-11).

AC2 below is satisfied by either a returned plan **or** an explicit operator `auto_approve`; either
way AC3 holds — the mutation is logged and committed.

### 3.2 The approval channel ([[010-agent-approval-channel]])

An approval request may also come from the **agent's own judgment**, not only from the deterministic
plan-first path. It adds **no route**: the request rides `ChatDelta.interaction` and is answered
through the existing `POST /api/chat/interaction` (+ `/stream`) endpoints, exactly like any other
blocking interaction (010 FR-1/FR-3).

- With trust mode **off**, the interaction arrives `status="pending"`, kind `approval`, exactly one
  proposal, and is durable — answerable at `/api/chat/interaction` (010 FR-3).
- With trust mode **on**, the same interaction may appear on `ChatDelta.interaction` already decided:
  `status="resolved"`, `resolution="auto-approved"`. This is **context, not a question** — it is never
  stored as the pending interaction, so `GET /api/chat/interaction` returns `null` for it, and posting
  a response to its id is rejected like any resolved id ([[008-agent-user-interaction]] FR-16).
  Surfaces MUST render it without selectable options (010 FR-5).
- Answering an agent-raised approval or clarification **resumes the turn**, so the response completes
  the requested work rather than acknowledging the choice (010 FR-7).

The agent's surface is unchanged in what it may *decide*: no tool grants an approval, answers an
interaction, or reads/sets trust mode (010 FR-2; §3.1's structural exclusions still hold).

## 4. Acceptance Criteria

- AC1: Every Chat capability has an API equivalent.
- AC2: A call for consequential work never executes silently. It resolves to **one of three**
  outcomes ([[011-maker-checker-approval]] FR-15): it **asks** (returning the accumulated, scored
  operation list for approval), it is **auto-approved** under standing consent or recorded precedent
  (and says so in the reply), or it is **declined**. Executing without one of these having been
  satisfied is a defect.
- AC2b: Every surface — REST and chat alike — reaches execution **only** through the concierge
  ([[011-maker-checker-approval]] FR-23), and the same request behaves identically on both (P9).
- AC3: API-initiated mutations pass through the risk engine and produce Git commits.
- AC4: External PM actions via API occur only when explicitly requested.
- AC5: The API cannot reach storage except through the shared capability layer.
- AC6: Skill capabilities have both surfaces — catalog, installed-list, and import are each a
  `/api/*` endpoint and reachable from chat (chat import stays plan-first) — see
  [[005-skill-import]] FR-11.
- AC7: The chat agent's MCP tool set mirrors the capability layer minus the exclusion set:
  every capability is an agent tool except the structurally-excluded chat surface and the
  configurable blacklist (default `chat, upload, create_workspace`); each agent tool is bound to
  the active workspace; REST is unaffected by the blacklist — see [[006-mcp-capability-tools]].
