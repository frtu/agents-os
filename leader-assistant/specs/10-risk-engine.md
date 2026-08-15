---
id: 202608132112-10
title: Risk Engine
spec: 10-risk-engine
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [risk, rules-engine, branching, governance, extensibility]
traceability:
  readme: ["§7 Risk-Based Branching", "§22 Risk Engine"]
  references: ["_references_/10-internal-storage/wiki-schema.md#contradiction-handling"]
related:
  - "[[04-knowledge-ingestion]]"
  - "[[08-specification-lifecycle]]"
  - "[[11-git-workflow]]"
  - "[[01-principles]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# Risk Engine

Not every change goes directly to `main`. The assistant evaluates every proposed mutation with an **extensible risk-rule engine**. Risk rules are configuration/domain objects — **not** hard-coded `if` statements scattered through the app.

## 1. Decision Flow

```text
Change → Risk Evaluation
   ├── safe ──► commit to main
   └── risky ──► feature/{feature-name} → commits → user review → merge
```

The assistant MUST NOT silently merge a risky branch without the approval policy being satisfied ([[11-git-workflow]]).

## 2. RiskRule Structure

```text
RiskRule
├── id           # e.g. CONTRADICTION_WITH_EXISTING_KNOWLEDGE
├── description  # human-readable intent
├── scope        # what it inspects (concept, spec, source, batch)
├── condition    # predicate over the proposed mutation
├── severity     # informational | warning | blocking
└── action       # commit-main | feature-branch | require-approval | reject
```

The rule set MUST be extensible **without redesigning the ingestion engine** ([[04-knowledge-ingestion]]).

## 3. Initial Rule Catalog (examples, not final)

| id | Triggers on |
|----|-------------|
| `CONTRADICTION_WITH_EXISTING_KNOWLEDGE` | proposed change contradicts existing knowledge |
| `CHANGE_RELIABLE_CONCEPT` | modification of a `reliable` concept |
| `LARGE_KNOWLEDGE_MUTATION` | large-scale / many-page changes |
| `DELETE_REFERENCED_CONCEPT` | deletion of a highly `referenced-to` concept |
| `MODIFY_APPROVED_SPEC` | modification of an approved specification ([[08-specification-lifecycle]]) |
| `LOW_PROVENANCE_CONFIDENCE` | changes with insufficient provenance |

Future candidates: modification of many interconnected concepts, changes affecting many Areas, conflicting sources, potentially destructive changes, semantic uncertainty.

## 4. Extensibility Requirements

- Rules are declared as data (config/domain objects), loadable without code changes to engines.
- New rules compose; evaluation returns the highest-severity matched action.
- Each rule evaluation is auditable (logged with rule id, matched condition, chosen action).

## 5. Acceptance Criteria

- AC1: Every proposed mutation is evaluated by the rule engine before landing.
- AC2: Adding a new rule requires no change to ingestion/specification engines.
- AC3: `risky` results route to `feature/{feature-name}`; `safe` results commit to `main`.
- AC4: A risky branch is never auto-merged without the approval policy satisfied.
- AC5: Each evaluation is recorded (rule id, severity, action) for audit ([[17-observability]]).
