---
id: 202608132112-16
title: Workflows & Knowledge Operations
spec: 16-workflows
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [workflows, operations, orchestration, dreaming, ingest, query, lint]
traceability:
  readme: ["§12 Knowledge Operations", "§13 Specification Generation Pipeline"]
  references: ["_references_/10-internal-storage/wiki-schema.md#operations"]
related:
  - "[[04-knowledge-ingestion]]"
  - "[[06-conversations]]"
  - "[[07-specification-model]]"
  - "[[17-observability]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# Workflows & Knowledge Operations

The Workflow/Execution Engine ([[12-assistant]]) orchestrates the four knowledge operations and the specification-generation pipeline.

## 1. The Four Operations

| Operation | Purpose | Trigger |
|-----------|---------|---------|
| **Dreaming** | Compact daily sessions into `wiki/sources/_daily_/` digests | end of day / on demand |
| **Ingest** | Process raw sources into wiki knowledge | new file in `raw/` |
| **Query** | Answer questions from the wiki with citations | user question |
| **Lint** | Health-check the wiki (contradictions, orphans, staleness) | periodic / on demand |

Dreaming → [[06-conversations]]. Ingest → [[04-knowledge-ingestion]]. Lint → [[17-observability]].

## 2. Query Operation (wiki-schema §Query)

1. Read `wiki/portal.md` to find relevant pages.
2. Read the relevant wiki pages.
3. Synthesize an answer with `[[wikilink]]` citations.
4. If a valuable artifact results (comparison/analysis/new connection), offer to save it to `wiki/synthesis/`.
5. If saved, update portal and log.

## 3. Specification-Generation Pipeline

```text
Knowledge change → impact analysis → identify affected specifications
  → generate/update draft documents → link specifications
  → consistency checks → risk evaluation → Git commit / feature branch
```

Continuous generation means specs evolve as the knowledge base evolves ([[07-specification-model]]).

## 4. Lint Frequency (wiki-schema)

- After every 10 ingests (catch cross-reference gaps while fresh).
- Monthly minimum (catch stale claims / orphans).
- Before any major query or synthesis (ensure a healthy wiki).

## 5. Orchestration Rules

- Every operation appends a `wiki/log.md` entry and produces Git commits where it mutates state.
- Operations invoke the risk engine before landing mutations on `main`.
- Autonomous operations (ingest/dreaming/lint) run without a plan; consequential work routes through [[09-planning]].

## 6. Acceptance Criteria

- AC1: All four operations are implemented and independently invocable (Chat + API).
- AC2: Query answers always cite wiki pages via `[[wikilinks]]`.
- AC3: Lint runs on the defined schedule and reports findings before offering fixes.
- AC4: The spec-generation pipeline runs end-to-end on a project-relevant knowledge change.
- AC5: Every operation logs and (when mutating) commits.
