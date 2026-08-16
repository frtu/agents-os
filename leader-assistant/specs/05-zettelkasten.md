---
id: 202608132112-05
title: Zettelkasten Knowledge Management
spec: 05-zettelkasten
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [zettelkasten, atomicity, connections, status-lifecycle, staleness]
traceability:
  readme: ["§11 Zettelkasten Model", "§19 Knowledge Engine"]
  references: ["_references_/10-internal-storage/wiki-schema.md#zettelkasten-management", "_references_/0-context/Introduction to the Zettelkasten Method • Zettelkasten Method.md"]
related:
  - "[[02-domain-model]]"
  - "[[04-knowledge-ingestion]]"
  - "[[07-specification-model]]"
  - "[[17-observability]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# Zettelkasten Knowledge Management

The `vault/wiki/` layer follows Zettelkasten principles so knowledge compounds over time. The Knowledge Engine ([[12-assistant]]) enforces these rules.

## 1. Identity
Every wiki page has a **stable unique identifier**, preferably time-based `202608120746` (YYYYMMDDHHMM), stored in frontmatter (not necessarily the filename). Filenames may change; the ID must not. IDs enable stable references as titles evolve.

## 2. Atomicity
Each page represents **one meaningful knowledge building block**. Avoid "everything about X" pages; split broad topics. Atomicity is a guiding principle — structure notes / MOCs intentionally aggregate.

## 3. Connections
Value comes from **relationships**. Every new page links to ≥1 existing page and states *why* the connection exists.
- Bad: `See also: [[Kafka]]`
- Good: `Kafka provides exactly-once delivery guarantees needed for [[idempotency]]`

## 4. Status Lifecycle (concept maturity)

```text
draft → used → reliable
        ▲         │
        └── big correction (demote)
```

| Status | Criteria | Meaning |
|--------|----------|---------|
| `draft` | new or substantially changed | insufficient validation |
| `used` | `usage-count ≥ 3` (referenced by ≥3 outputs) | practically useful |
| `reliable` | `clean_uses > 8` (used >8 times without a big correction) | validated knowledge |

Status is **evidence-based**, computed from two frontmatter fields — never asserted by hand:

- **counter** — `usage-count`: total artifacts that have cited this concept.
- **reference** — `referenced-to`: the list of `[[links]]` to those artifacts.
- **`last-correction`** — the date of the most recent big correction (empty until the first one).

**Lifecycle math (authoritative):** `clean_uses` = uses counted since `last-correction` (or since creation if none). `status = reliable` if `clean_uses > 8`; else `used` if `usage-count ≥ 3`; else `draft`.

**Big correction & demotion:** a *big correction* is a substantive change to the concept's body (not a typo/format fix). It sets `last-correction = today`, which restarts the clean-use streak and **demotes `reliable → used`** until evidence re-accumulates. Only the lifecycle engine ([[12-assistant]]) writes these fields.

## 5. referenced-to (reference) + usage-count (counter)
Track where concepts are actually used (distinct from conceptual `[[links]]`):

```yaml
status: reliable
usage-count: 9            # counter — bumped once per citing artifact
referenced-to:            # reference — one [[link]] per citing artifact
  - "[[spec-product-requirements]]"
  - "[[spec-workflow-model]]"
last-correction: 2026-08-10   # empty until the first big correction
```

- `[[Concept]]` = these are related.
- `referenced-to` + `usage-count` = this concept contributed to producing these artifacts (drives maturity).

## 6. Structure Notes (MOCs)
Organize other pages: `vault/wiki/portal.md` (master entry), `vault/wiki/product/specs/*.md` (03+ spec MOCs), category hubs. Support hierarchical (nested), sequential (a→b→c argument chains), and cross-category (semilattice) structures.

## 7. Contradiction Handling
1. Note the contradiction explicitly. 2. Cite both sources. 3. If resolution is clear → update the page. 4. If unclear → create a `vault/wiki/synthesis/` page analyzing the conflict. 5. Consider risk-based branching for significant contradictions ([[10-risk-engine]]).

## 8. Staleness Detection (lint inputs)
Flag: `reliable` pages that required major corrections; `draft` pages used many times; sources superseded by newer info; orphan pages (no inbound links); important topics lacking a page. See [[17-observability]] / lint.

## 9. Knowledge Hygiene
- **Provenance**: every concept traces back through `vault/wiki/sources/ → vault/raw/`.
- **Deduplication**: search for existing coverage before creating a page.
- **Refactoring**: split pages that outgrow atomicity.
- **Deprecation**: mark obsolete pages rather than deleting (maintain history).

## 10. Acceptance Criteria
- AC1: Every wiki page has a stable `id` and valid frontmatter.
- AC2: No new page is created without at least one justified inbound/outbound link.
- AC3: Concept `status` transitions are computed from `usage-count` / `referenced-to`, and a big correction sets `last-correction` and demotes `reliable → used`.
- AC4: Duplicate-topic pages are detected and merged during lint.
- AC5: Contradictions are always recorded with both sources cited.
