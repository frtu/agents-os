---
id: 202608160930-21
title: PO/PM Outputs (secondary capability)
spec: 21-outputs
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [outputs, templates, po-pm, artifacts, reuse-before-create]
traceability:
  readme: ["§11 Assistant Responsibilities", "§13 Output Types"]
  references: ["_references_/10-internal-storage/wiki-schema.md"]
related:
  - "[[00-product-vision]]"
  - "[[00-product-vision-contradiction]]"
  - "[[07-specification-model]]"
  - "[[15-integrations]]"
  - "[[05-zettelkasten]]"
Created: 2026-08-16
Last Updated: 2026-08-16
---

# PO/PM Outputs (Secondary Capability)

> **Extension doc.** Specifications remain the **primary** product output ([[00-product-vision]], [[07-specification-model]], Constitution P11). This doc adds the broader Product-Owner / Project-Manager artifact catalog as a **secondary**, template-driven capability. Scope decision recorded in [[00-product-vision-contradiction]].

## 1. Purpose

Let the assistant produce concrete PO/PM artifacts on request — grounded in `wiki/` knowledge, reusing externalized templates, and feeding usage back into concept maturity. This is the "knowledge application" half of the product, subordinate to continuous specification generation.

## 2. Output Types (initial catalog)

| Output | Template | Notes |
|--------|----------|-------|
| Meeting summary | `templates/meeting-summary.md` | decisions, action items, owners |
| Document review & comment | `templates/document-review.md` | gaps, risks, contradictions vs `wiki/` |
| Engineering ticket | `templates/engineering-ticket.md` | **Why / Who / What / Acceptance criteria** |
| Product strategy brief | `templates/product-strategy.md` | options + recommendation |
| Project summary / status | `templates/project-summary.md` | RAID, milestones, decisions |

The catalog is extensible; new types add a template (Constitution P7).

## 3. Reuse-Before-Create (Constitution P7)

1. On any output request, search the **externalized root `templates/`** for the closest match and reuse it.
2. If none fits, **propose** a new template; save to `templates/` only on user approval; then produce.
3. State the template used (or "new proposed") in the artifact/report.

Templates live outside the vault so humans review and evolve them ([[03-vault]] §Templates, [`templates/README`](../templates/README.md)). "Closest match" scoring is open — [[001-leader-assistant/plan-tbd|plan-tbd]] TBD-4.

## 4. Grounding, Traceability & Promotion (Constitution P5/P6)

- Every artifact is written to `output/` as Markdown with frontmatter.
- Every artifact **cites** the `wiki/` concepts it used via `[[wikilinks]]`.
- For each cited concept, the `lifecycle` engine appends the artifact to `referenced-to` (the **reference**) and increments `usage-count` (the **counter**), then recomputes `status`. See [[05-zettelkasten]].
- If producing an artifact reveals a wrong concept and it is substantively revised, that is a **big correction** (records `last-correction`, demotes `reliable → used`).
- A production entry is appended to `wiki/log.md` (`## [YYYY-MM-DD] output | <Title>`), never editing prior entries.

## 5. Knowledge Grounding Rule

Outputs are grounded in `wiki/`. If required knowledge is absent, the assistant **reports the gap** (and may suggest ingestion) rather than fabricating.

## 6. Relationship to Specifications & Integrations

- Specifications are generated continuously and are not "produced on request" like these artifacts.
- PO/PM outputs may be pushed to an external PM system only on explicit user demand ([[15-integrations]]).
- Whether outputs feed the spec graph or only the knowledge feedback loop is open — see [[00-product-vision-contradiction]] and [[clarification]].

## 7. Acceptance Criteria

- AC1: A request with a matching template reuses it and records the choice; no match triggers a gated new-template proposal.
- AC2: Each catalog output type produces a well-formed artifact in `output/`.
- AC3: A produced ticket contains Why / Who / What / Acceptance criteria at minimum.
- AC4: Every artifact cites its concepts; each cited concept gains a `referenced-to` back-link + incremented `usage-count`.
- AC5: A threshold-crossing concept is promoted; a big correction during production demotes it.
- AC6: A production entry is appended to `log.md` without altering prior entries.
- AC7: Missing knowledge is reported, not fabricated.
