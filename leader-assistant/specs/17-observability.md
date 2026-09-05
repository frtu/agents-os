---
id: 202608152112-17
title: Observability — Portal, Log & Health
spec: 17-observability
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [observability, portal, log, lint, audit, index, tracing, langfuse]
traceability:
  readme: ["§27 Portal and Log", "§12 Knowledge Operations"]
  references: ["_references_/10-internal-storage/wiki-schema.md#index-format", "_references_/10-internal-storage/wiki-schema.md#log-format", "_references_/0-context/llm-wiki.md"]
related:
  - "[[03-workspace]]"
  - "[[05-zettelkasten]]"
  - "[[11-git-workflow]]"
  - "[[16-workflows]]"
  - "[[013-langfuse-observability]]"
Created: 2026-08-15
Last Updated: 2026-09-04
---

# Observability — Portal, Log & Health

The wiki is observable through two special files plus lint and Git. These provide navigation, an audit timeline, and health signals without external infrastructure.

## 1. Portal (`vault/wiki/portal.md`)

Master catalog of every wiki page. Content-oriented. Updated on **every ingest**.

- One line per page: `- [[page-name|Page Name]] — one-line summary` (<120 chars).
- Grouped by category headers: Product · People · Concepts · Resources · Projects · Synthesis · Sources.
- Read first when answering a query ([[16-workflows]]).

## 2. Log (`vault/wiki/log.md`)

Chronological, **append-only** operational record. Never edit existing entries.

- Entry format: `## [YYYY-MM-DD] operation | Title` + brief description.
- Operations: `ingest`, `query`, `lint`, `synthesis`, `dreaming`, `spec`.
- Parseable with unix tools: `grep "^## \[" vault/wiki/log.md | tail -5`.

## 3. Lint (health check)

Scan for: contradictions between pages; stale claims superseded by newer sources; orphan pages (no inbound links); important topics lacking a page; missing cross-references; pages in the wrong subdirectory; data gaps fillable by web search. Report findings, offer fixes, then log `## [YYYY-MM-DD] lint | Summary`.

## 4. Audit & Metrics (derived)

- **Risk audit**: each risk evaluation records rule id, severity, action ([[10-risk-engine]]).
- **Provenance audit**: any concept traces `wiki → sources → raw` ([[02-domain-model]] §5).
- **Maturity signal**: concept `status` distribution and `referenced-to` counts ([[05-zettelkasten]]).
- **Git as timeline**: commits/branches provide the authoritative change history ([[11-git-workflow]]).

## 5. Application Tracing (Langfuse)

Distinct from sections 1–4, which observe the **wiki's own knowledge**: this section observes the
**app's own model calls** — an external, optional integration, detailed in [[013-langfuse-observability]].

- Every `claude_agent_sdk.query()` call site (the chat turn, both ingest phases, the judge's risk
  review) is wrapped in a Langfuse generation/span (`app/tracing.py`), capturing input, output,
  token usage and cost from the SDK's own `ResultMessage`.
- **FR-T1:** Tracing MUST be a no-op — no network call, no exception, no behavioural change —
  whenever `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` are unset (the default; always true for the
  automated test suite, spec 03-workspace §0).
- **FR-T2:** A chat turn's generation MUST be tagged with the conversation id as the Langfuse
  session id, so every turn of one conversation groups into one session in the Langfuse UI.
- **FR-T3:** Ingest's two phases MUST nest under one parent trace, not report as two unrelated
  traces.
- **FR-T4:** Tracing MUST reach zero external systems beyond the configured Langfuse instance —
  no vault/wiki write, no `log.md` entry (this is process telemetry, not knowledge, P1/P10).

## 6. Acceptance Criteria

- AC1: `portal.md` is updated on every ingest and stays within the one-line/<120-char format.
- AC2: `log.md` is append-only; existing entries are never modified.
- AC3: Lint produces a findings report on schedule and logs each pass.
- AC4: Any wiki concept's provenance chain is reconstructable on demand.
- AC5: Risk decisions are auditable from the log/Git.
- AC6: With Langfuse unconfigured, the full test suite passes unchanged (FR-T1).
- AC7: With Langfuse configured, a chat turn and an ingest produce traces in the local Langfuse UI
  (FR-T2/FR-T3), with token usage/cost populated from the SDK's `ResultMessage`.
