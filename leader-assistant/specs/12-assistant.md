---
id: 202608152112-12
title: Assistant Architecture
spec: 12-assistant
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [architecture, engines, components]
traceability:
  readme: ["§18 Assistant Architecture", "§19 Knowledge Engine", "§20 Ingestion Engine", "§21 Specification Engine", "§22 Risk Engine"]
  references: []
related:
  - "[[04-knowledge-ingestion]]"
  - "[[07-specification-model]]"
  - "[[10-risk-engine]]"
  - "[[13-api]]"
Created: 2026-08-15
Last Updated: 2026-08-15
---

# Assistant Architecture

Logical components (not necessarily separate deployable services). Business logic lives **below** the interface layer so Chat and API share it ([[13-api]], [[14-chat]]).

## 1. Component Map

```text
Assistant
├── Conversation Manager      → captures sessions; feeds dreaming ([[06-conversations]])
├── Knowledge Engine          → search/relate/track knowledge ([[05-zettelkasten]])
├── Ingestion Engine          → raw → wiki pipeline ([[04-knowledge-ingestion]])
├── Zettelkasten Manager      → identity/atomicity/status/referenced-to
├── Specification Engine      → specs + graph ([[07-specification-model]])
├── Planning Engine           → plan-first interaction ([[09-planning]])
├── Risk Engine               → rule-driven branching ([[10-risk-engine]])
├── Workflow/Execution Engine → orchestrates operations ([[16-workflows]])
├── Git/Vault Manager         → commits/branches ([[11-git-workflow]])
└── Integration Manager       → external PM on demand ([[15-integrations]])
```

## 2. Knowledge Engine (README §19)

Responsibilities: search Vault · identify relevant concepts · resolve Obsidian links · inspect Areas · identify source provenance · detect concept relationships · identify contradictions · track concept usage · evaluate concept maturity · maintain indexes.

## 3. Ingestion Engine (README §20)

detect raw documents · classify source type · normalize · generate source documents · extract knowledge candidates · compare against existing knowledge · generate wiki changes · invoke risk evaluation · commit or branch. Detailed in [[04-knowledge-ingestion]].

## 4. Specification Engine (README §21)

maintain spec documents · identify gaps · create drafts · update from new knowledge · maintain cross-document links · detect inconsistencies · track lifecycle · connect specs to concepts · support review/approval. Detailed in [[07-specification-model]].

## 5. Layering Rule (invariant)

Chat must not implement capabilities that cannot be invoked through the API. The API must not bypass the planning/risk/knowledge model. All engines are reachable only through the shared capability layer.

## 6. Acceptance Criteria

- AC1: Every listed engine exists as an addressable capability behind the interface layer.
- AC2: No capability is Chat-only or API-only.
- AC3: Engines interact only through defined capabilities (no direct interface-to-storage shortcuts).
- AC4: Each engine's responsibilities from README §19-22 are covered by its detailed spec.
- AC5: All consequential executions are gated by the **maker–checker** stack of
  [[011-maker-checker-approval]], not by a two-engine check: every request enters through the
  **concierge** (FR-23), the **execution** layer announces each operation it attempts (FR-2), the
  **workflow reporting** layer scores and accumulates them and pauses at the first gate (FR-11/FR-12),
  and the **checker** returns approve / decline / ask under a deterministic filter (FR-17). Planning
  and Risk remain the engines that *describe* the work and *score* it; they no longer *grant* it.
- AC6: The three layers are independent — no layer imports another's internals, and each is testable
  with the other two replaced by default stubs ([[011-maker-checker-approval]] FR-34/FR-35).
