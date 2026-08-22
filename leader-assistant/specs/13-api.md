---
id: 202608132112-13
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
Created: 2026-08-13
Last Updated: 2026-08-13
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

## 4. Acceptance Criteria

- AC1: Every Chat capability has an API equivalent.
- AC2: API calls for consequential work return a plan for approval rather than executing immediately.
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
