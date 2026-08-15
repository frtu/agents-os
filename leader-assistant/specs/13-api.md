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
- **Integration**: request an external PM action (user-initiated) — see [[15-integrations]].

Exact endpoint shapes are defined at implementation time; the constraint is capability parity, not a specific transport.

## 3. Governance Through the API

Requests that are consequential still flow through [[09-planning]] and [[10-risk-engine]]; the API returns plans/risk outcomes rather than silently executing.

## 4. Acceptance Criteria

- AC1: Every Chat capability has an API equivalent.
- AC2: API calls for consequential work return a plan for approval rather than executing immediately.
- AC3: API-initiated mutations pass through the risk engine and produce Git commits.
- AC4: External PM actions via API occur only when explicitly requested.
- AC5: The API cannot reach storage except through the shared capability layer.
