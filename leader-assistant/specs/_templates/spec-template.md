# Feature Specification: [FEATURE NAME]

**Feature ID:** `NNN-short-name`
**Status:** Draft | In Review | Approved
**Created:** YYYY-MM-DD · **Last Updated:** YYYY-MM-DD

> Describes **what** and **why**, never **how**. No tech stack, no code, no file layout — those belong in `plan.md`. Written to be readable by a non-engineer stakeholder.
>
> In this repo the **primary spec is the 21-document set** (`specs/00`–`specs/20`, plus `21-outputs`). A feature `spec.md` may reference those docs rather than restating them.

## Summary

One paragraph: what this feature is and the value it delivers.

## Goals

- What this feature must achieve.

## Non-Goals

- Explicitly out of scope (prevents scope creep).

## User Scenarios

- **Scenario 1 — [name]:** As a [role], when I [action], the assistant [observable behavior], so that [value].

## Functional Requirements

Numbered, testable, unambiguous. Mark unknowns with `[NEEDS CLARIFICATION: …]` and mirror them into [`clarification.md`](../clarification.md).

- **FR-1:** The system MUST …

## Key Entities & Concepts

Domain nouns this feature introduces or touches (workspaces, concepts, outputs, templates, status, …). Describe them, not their storage.

## Constraints & Assumptions

- Constraints (from [`memory/constitution.md`](../../memory/constitution.md) or environment).
- Assumptions that, if wrong, change the design.

## Acceptance Criteria

- [ ] AC-1 …

## Open Questions

- `[NEEDS CLARIFICATION: …]` → also listed in [`clarification.md`](../clarification.md)

## Review Checklist

- [ ] No implementation details (how) leaked into this spec.
- [ ] Every requirement is testable.
- [ ] Scenarios cover the golden path and key edge cases.
- [ ] Complies with `memory/constitution.md`.
- [ ] Any local↔remote conflict captured in a `*-contradiction.md`, not silently resolved.
