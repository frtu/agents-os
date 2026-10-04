# Feature Specification: [FEATURE NAME]

**Feature ID:** `NNN-short-name`
**Status:** Draft | In Review | Approved
**Created:** YYYY-MM-DD · **Last Updated:** YYYY-MM-DD

> Describes **what** and **why**, never **how**. No tech stack, no code, no file
> layout — those belong in `plan.md`. Readable by a non-engineer stakeholder.
>
> The **area specs** (`_specs_/overview`, `domain`, `planning`, `execution`, `api`,
> …) are the primary spec. A feature spec references them rather than restating
> them, and lists every area spec it amends under **Amends**.

**Amends:** [planning/…](../../planning/…) · [api/rest-api.md](../../api/rest-api.md) · …

## Summary

One paragraph: what this feature is and the value it delivers to a leader.

## Goals

- What this feature must achieve.

## Non-Goals

- Explicitly out of scope (prevents scope creep).

## User Scenarios

- **Scenario 1 — [name]:** As a [leader / operator], when I [action], the
  Control Center [observable behaviour], so that [value].

## Functional Requirements

Numbered, testable, unambiguous. Mark unknowns with `[NEEDS CLARIFICATION: …]`
and mirror them into [`clarification.md`](../../clarification.md).

- **FR-1:** The system MUST …

## Key Entities & Concepts

Domain nouns this feature introduces or touches (use the
[glossary](../../overview/glossary.md) verbatim). Describe them, not their storage.

## Commands, Queries & Events

Business commands and projections this feature adds (names only, no transport):
`StartX` → emits `XStarted`; query `X board`.

## Constraints & Assumptions

- Constraints (from [`constitution.md`](../../constitution.md) or environment).
- Assumptions that, if wrong, change the design.

## Acceptance Criteria

- [ ] AC-1 …

## Open Questions

- `[NEEDS CLARIFICATION: …]` → also listed in [`clarification.md`](../../clarification.md)

## Review Checklist

- [ ] No implementation details (how) leaked into this spec.
- [ ] Every requirement is testable and has an id.
- [ ] Scenarios cover the golden path and key edge cases.
- [ ] Complies with [`constitution.md`](../../constitution.md).
- [ ] Every amended area spec is listed under **Amends**.
