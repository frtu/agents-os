# Tasks: [FEATURE NAME]

**Feature ID:** `NNN-short-name` · **Plan:** [`plan.md`](plan.md)
**Last Updated:** YYYY-MM-DD

> Ordered, actionable build steps derived from `plan.md`. Each task is small
> enough to complete and verify independently. Mark `[P]` for tasks that can run
> in parallel (no shared files / no dependency).

## Legend

- `[ ]` pending · `[x]` done
- `[P]` parallelizable
- Each task references the spec item it satisfies (FR-n, AC-n, or an invariant
  from [`testing/testing.md`](../../testing/testing.md)).

## Spec

- [ ] T001 Write `spec.md`, `plan.md`, `tasks.md`; amend the area specs listed
  under **Amends** (and `api/rest-api.md` / `api/realtime.md` if the contract
  changes).

## Backend

- [ ] T010 Domain models / enums (FR-…)
- [ ] T011 Application commands / queries (FR-…)
- [ ] T012 [P] Workflow port / adapter (FR-…)
- [ ] T013 Infra: SQLite schema + seed (FR-…)
- [ ] T014 API routes + schemas + realtime messages (FR-…)

## Frontend

- [ ] T020 `types/domain.ts` in lockstep with `models.py` (P6)
- [ ] T021 [P] `api/http.ts` + `api/mock/` + hooks (FR-…)
- [ ] T022 [P] Feature UI (FR-…)

## Validation

- [ ] T030 Backend tests mapping to every AC (`uv run --extra dev pytest`) (AC-…)
- [ ] T031 Frontend `npm run typecheck && npm run build`
- [ ] T032 Run the stack per `getting-started.md` and verify the scenarios

## Dependencies

Ordering constraints, e.g. "T014 blocked by T011".
