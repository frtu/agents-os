# Tasks: [FEATURE NAME]

**Feature ID:** `NNN-short-name` · **Plan:** [`plan.md`](plan.md)
**Last Updated:** YYYY-MM-DD

> Ordered, actionable build steps derived from `plan.md`. Each task is small enough to complete and verify independently. Mark `[P]` for tasks that can run in parallel (no shared files / no dependency). Keep tasks tied to the **local spec** — discard disposable, illustrative endpoint tasks.

## Legend

- `[ ]` pending · `[x]` done
- `[P]` parallelizable
- Each task references the spec/plan item it satisfies (FR-n, AC-n, or an invariant from [`20-testing`](../20-testing.md)).

## Setup

- [ ] T001 …

## Core

- [ ] T010 … (FR-1)
- [ ] T011 [P] … (FR-2)

## Integration

- [ ] T020 …

## Validation

- [ ] T030 Verify AC-1 …

## Dependencies

Note ordering constraints, e.g. "T020 blocked by T010, T011".
