---
id: 202608132112-19
title: Non-Functional Requirements
spec: 19-non-functional
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [non-functional, portability, scalability, non-goals]
traceability:
  readme: ["§28 Core Invariants", "§29 Initial Non-Goals", "§10 Knowledge Layers"]
  references: ["_references_/0-context/llm-wiki.md", "_references_/10-internal-storage/wiki-schema.md#tools"]
related:
  - "[[01-principles]]"
  - "[[03-vault]]"
  - "[[17-observability]]"
  - "[[20-testing]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# Non-Functional Requirements

## 1. Portability & Independence

- The Vault is **plain Markdown + Git**; it must remain readable and usable without any proprietary software (wiki-schema §Git as Memory).
- Markdown/Obsidian is the canonical human-readable representation; vector embeddings are **not** the canonical knowledge model ([[01-principles]] Non-Goals).
- The knowledge base must not depend on a proprietary database.

## 2. Scalability

- Navigation via `portal.md` works at moderate scale (~100 sources, hundreds of pages).
- Beyond that, an on-device search tool (e.g. `qmd`) may be introduced without changing the storage model ([[17-observability]], wiki-schema §Tools).
- A single ingest touching 10–15 pages is normal and must remain performant.

## 3. Maintainability

- Risk rules are data, not scattered `if` statements ([[10-risk-engine]]) — extensible without redesign.
- Business logic lives below the interface layer for Chat/API parity ([[12-assistant]]).
- Atomic, well-linked pages keep maintenance cost near zero ([[05-zettelkasten]]).

## 4. Reliability & Auditability

- Every mutation is committed; history/rollback available via Git.
- `log.md` append-only; `portal.md` consistent after every ingest.

## 5. Usability

- Human stays in control of consequential work; assistant is autonomous for bookkeeping ([[09-planning]]).
- Answers cite sources; drafts and alternatives are presented for feedback.

## 6. Non-Goals (README §29)

Will NOT: replace an external PM platform; be a general Jira/Linear alternative; auto-sync every PM artifact; require human approval for all knowledge changes; depend on a proprietary DB; replace Markdown/Obsidian; treat embeddings as canonical; autonomously execute arbitrary external actions.

## 7. Acceptance Criteria

- AC1: The Vault is fully usable with only a text editor + Git.
- AC2: Introducing search tooling requires no change to the Markdown/Git storage model.
- AC3: Adding a risk rule requires no engine redesign.
- AC4: No capability requires a proprietary database or embedding store to function.
- AC5: All stated non-goals are respected by the implementation.
