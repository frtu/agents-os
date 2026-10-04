# Tasks: API Console

**Feature ID:** `001-api-console` · **Plan:** [`plan.md`](plan.md)
**Last Updated:** 2026-10-04

## Spec

- [x] T001 Write `spec.md`, `plan.md`, `tasks.md`; amend `frontend/frontend.md`
  (Navigation + API Console view); add the feature to `features/README.md`.

## Frontend

- [x] T010 [P] `features/console/openapi.ts` — load + flatten operations, example bodies (FR-1, FR-2, FR-14)
- [x] T011 [P] `features/console/client.ts` — raw send + id collection (FR-3, FR-5)
- [x] T012 `features/console/scenarios.ts` — four scenarios + runner (FR-7..FR-11)
- [x] T013 `Explorer.tsx`, `ScenarioPanel.tsx`, `EventLog.tsx`, `pages/ConsolePage.tsx` (FR-2..FR-6, FR-12)
- [x] T014 Route `/console` + sidebar entry; proxy `/openapi.json` (FR-13)

## Backend

- [x] T020 `tests/test_api_console_scenarios.py` — replay each scenario's request
  sequence against the app (AC-6, AC-7, AC-8)

## Validation

- [x] T030 `uv run --extra dev pytest`
- [x] T031 `npm run typecheck && npm run build`
- [x] T032a Headless run of the console modules (`openapi.ts`, `client.ts`,
  `scenarios.ts`, bundled with esbuild) against a live in-memory backend: 59
  operations loaded; preview example accepted (AC-2); 404 detail shown (AC-3);
  ids collected (AC-4); all four scenarios pass (AC-6); no leftovers, Schedule
  Archived (AC-8); backend-down reasons reported (AC-10).
- [ ] T032b Visual check in the browser: layout, history re-display (AC-5), event
  log during the Schedule scenario (AC-9), sidebar entry (AC-10).

## Dependencies

T013 blocked by T010–T012; T020 independent.
