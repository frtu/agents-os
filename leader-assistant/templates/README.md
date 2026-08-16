# Output Templates

Externalized, human-owned **output templates** the assistant reuses when producing artifacts (per Constitution [`P7 — Reuse before create`](../memory/constitution.md)).

## Why this folder exists

Templates live at the repository root — **outside** any vault and outside the assistant's autonomous write paths — so humans can review, edit, and evolve them without touching knowledge or code. The assistant treats these as read-first, propose-before-changing.

## Reuse-before-create contract

1. On any output request, the assistant MUST first search this folder for the **closest matching** template and reuse it.
2. A new template is created only when no close match exists, and MUST be **proposed to the user** before being saved here and used.
3. The produced artifact (or its report) MUST state which template was used, or "new template proposed".

> How "closest match" is scored (declared output-type tag vs. filename/title similarity vs. semantic match) is an open decision — see [`specs/clarification.md`](../specs/clarification.md) and [`specs/001-leader-assistant/plan-tbd.md`](../specs/001-leader-assistant/plan-tbd.md).

## Template anatomy

Each template is Markdown with `{{placeholders}}` and short HTML-comment guidance. Keep them house-style, not exhaustive. Concepts pulled from `wiki/` are cited with `[[wikilinks]]`; every cited concept gains a `referenced-to` back-link and a `usage-count` increment (Constitution P5/P6).

## Seed templates

| File | Output type |
|------|-------------|
| [`meeting-summary.md`](meeting-summary.md) | Meeting / transcript summary (decisions, action items, owners) |
| [`document-review.md`](document-review.md) | Document review & comment (gaps, risks, contradictions) |
| [`engineering-ticket.md`](engineering-ticket.md) | Engineering ticket (Why / Who / What / Acceptance criteria) |
| [`product-strategy.md`](product-strategy.md) | Product strategy brief |
| [`project-summary.md`](project-summary.md) | Project summary / status |

See [`specs/21-outputs.md`](../specs/21-outputs.md) for how these fit the (secondary) PO/PM output capability. Specifications remain the primary product output ([`specs/07-specification-model.md`](../specs/07-specification-model.md)).
