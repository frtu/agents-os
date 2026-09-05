---
id: 202608152112-20
title: Testing & Acceptance
spec: 20-testing
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [testing, acceptance, invariants, verification]
traceability:
  readme: ["§28 Core Invariants", "§13 Specification Generation Pipeline", "§12 Knowledge Operations"]
  references: ["_references_/10-internal-storage/wiki-schema.md#operations"]
related:
  - "[[01-principles]]"
  - "[[04-knowledge-ingestion]]"
  - "[[10-risk-engine]]"
  - "[[16-workflows]]"
Created: 2026-08-15
Last Updated: 2026-08-15
---

# Testing & Acceptance

Verification is anchored to the **Core Invariants** ([[01-principles]] §2) and the per-spec acceptance criteria. Each invariant maps to at least one automated test.

## 1. Invariant Test Matrix

| Invariant | Test focus | Spec |
|-----------|-----------|------|
| Raw never rewritten | writes to `vault/raw/` are rejected | [[18-security]] |
| Provenance retained | chain `vault/raw→sources→vault/wiki` reconstructable | [[02-domain-model]], [[17-observability]] |
| Stable concept IDs | IDs persist across rename | [[05-zettelkasten]] |
| Atomicity | oversized pages flagged by lint | [[05-zettelkasten]] |
| `[[wikilinks]]` for relations | no raw file paths in page bodies | [[03-workspace]] |
| `referenced-to` tracked | usage counts drive `status` | [[05-zettelkasten]] |
| Auto ingestion | new `vault/raw/` file triggers pipeline | [[04-knowledge-ingestion]] |
| Conversations persisted | sessions written; dreaming digests produced | [[06-conversations]] |
| Mutations → commits | every mutation commits | [[11-git-workflow]] |
| Risky → feature branch | risky mutation branches; no auto-merge | [[10-risk-engine]] |
| Portal updated on ingest | portal reflects new pages | [[17-observability]] |
| Log append-only | existing entries immutable | [[17-observability]] |
| Specs are linked | no orphan specs | [[07-specification-model]] |
| Drafts evolve continuously | knowledge change → draft update | [[07-specification-model]] |
| Approved not overwritten | edit opens revision, not overwrite | [[08-specification-lifecycle]] |
| Chat/API parity | capability parity holds both ways | [[13-api]], [[14-chat]] |
| External on demand only | no autonomous external actions | [[15-integrations]] |
| Plan-first | consequential work presents a plan | [[09-planning]] |
| Layers stay independent | layer 1 imports neither 2 nor 3; layer 2 does not import 3 | [[011-maker-checker-approval]] |
| Gate is not message-derived | an agent native-tool write is announced, scored, recorded | [[011-maker-checker-approval]] |
| Pause is enforced, not advised | denial comes from the hook; nothing runs past the gate | [[011-maker-checker-approval]] |
| Checker cannot widen authority | `approve` without consent or precedent downgrades to `ask` | [[011-maker-checker-approval]] |
| Checker fails closed | unavailable/malformed/cold-start resolves to `ask` | [[011-maker-checker-approval]] |
| Decline is final | declined operation never runs and is not re-asked in the run | [[011-maker-checker-approval]] |

## 2. Test Levels

- **Unit**: risk rule predicates; **scoring modifiers (base + weights, clamped 1–5)**; frontmatter/ID validation; wikilink formatting (incl. table-escaped `\|`).
- **Integration**: ingest pipeline end-to-end; dreaming→ingest promotion; spec-generation pipeline.
- **Operation**: query returns cited answers; lint detects seeded contradictions/orphans.
- **Governance**: risky change routes to branch; approved-spec edit opens a revision.
- **Parity**: each capability exercised via both Chat and API produces identical effects.
- **Layers in isolation** ([[011-maker-checker-approval]] FR-35): each of the three approval layers is
  tested with the other two replaced by their **default stubs** — allow-all permit (FR-3) and
  ask-checker (FR-13). A test that needs all three wired to exercise one of them is a coupling defect,
  not a test.

## 3. Acceptance Gate

A build is acceptable when: every Core Invariant test passes; each spec's own acceptance criteria pass; lint reports a clean (or explicitly-accepted) wiki; and Chat/API parity tests pass.

## 4. Acceptance Criteria

- AC1: Each Core Invariant has ≥1 automated test.
- AC2: The ingest and spec-generation pipelines have end-to-end tests.
- AC3: Governance (risk/branching/approval) is covered by tests.
- AC4: Parity tests assert identical Chat/API effects.
- AC5: CI runs the full matrix and blocks merges on failure.
- AC6: Each approval layer has tests that pass with the other two stubbed, and a static check asserts
  the import boundary ([[011-maker-checker-approval]] AC-1/AC-2).
