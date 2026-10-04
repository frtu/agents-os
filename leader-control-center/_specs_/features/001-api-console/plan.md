# Implementation Plan: API Console

**Feature ID:** `001-api-console` · **Spec:** [`spec.md`](spec.md)
**Status:** Draft
**Created:** 2026-10-04 · **Last Updated:** 2026-10-04

## Constitution Check

- [x] P1 Human first — no execution path changes; decisions are still answered via the decision endpoints.
- [x] P2 Planning immutable — scenarios only use commands; created Stories are left in place (FR-11).
- [x] P3 Command-oriented — only existing `/api/v1` commands and queries; no new endpoints.
- [x] P4 Engine independence — the console sees only what the API exposes.
- [x] P5 Provider independence — n/a.
- [x] P6 Contract lockstep — no contract change; the explorer reads the live OpenAPI, so it cannot drift.
- [x] P7 Spec first — this spec + plan precede code; code cites `spec 001 FR-N`.
- [x] P8 Tested — see Test Plan (frontend has no unit runner; scenarios double as live API checks).
- [x] P9 Error transparency — status + Problem+JSON `detail` shown for every failure (FR-3, FR-10, FR-14).
- [x] P10 Simplest thing — schema-driven, no per-endpoint UI; no new dependencies.
- [x] P11 Ubiquitous language — scenario names use domain terms (Schedule, Activity Definition, Story).

## Technical Context

- **Frontend only.** React + Tailwind primitives already in `components/ui`.
- **No new npm dependencies.**
- **Backend:** unchanged. OpenAPI is served at `/openapi.json` (FastAPI default).

## Architecture Overview

```text
pages/ConsolePage.tsx
  ├─ features/console/openapi.ts     load /openapi.json → Operation[]; example body from schema
  ├─ features/console/client.ts      raw fetch to /api/v1 → ConsoleResponse {status, ms, body}
  ├─ features/console/scenarios.ts   Scenario[] — steps as (ctx) => request, run sequentially
  ├─ features/console/Explorer.tsx   operation list + request builder + response view
  ├─ features/console/ScenarioPanel.tsx
  └─ features/console/EventLog.tsx   realtime.subscribe() → newest-first log
```

The console uses its own thin `fetch` wrapper, not `ApiClient`, because it must
reach arbitrary operations and always the real backend (spec Non-Goals). It reuses
`realtime` for the event log (works for both WS and mock stream).

## Components

- **openapi.ts** — `loadOperations()` fetches the OpenAPI document (URL derived
  from `VITE_API_BASE_URL`'s origin + `/openapi.json`), flattens `paths` into
  `{method, path, tag, summary, pathParams, queryParams, bodySchema}`, resolves
  `$ref`/`anyOf`. `exampleFor(schema)` builds a value: default → first enum →
  type placeholder; objects include required props + props with defaults. (FR-1, FR-2)
- **client.ts** — `send({method, path, query, body})` → `{status, ok, ms, body}`;
  never throws on HTTP errors; network errors become `status: 0` with the reason.
  `collectIds(body)` walks JSON for `id`/`…Id` strings. (FR-3, FR-5)
- **scenarios.ts** — `Scenario {id, title, description, steps}`; a step is
  `{name, run(ctx) → Request, check?(res, ctx) → string|void}`; `ctx` holds
  values discovered so far. `runScenario` executes steps in order, stops on the
  first non-2xx or failed check. Setup step reads `/initiatives` and
  `/workflow-definitions/{id}` to fill inputs (FR-9); `templateInput` is built
  from the definition's input schema with `exampleFor`. (FR-7..FR-11)
- **Explorer / ScenarioPanel / EventLog** — UI; history held in page state. (FR-6, FR-12)
- **Routing** — `/console` in `App.tsx`, *Console* in `Sidebar.tsx`. (FR-13)
- **vite.config.ts** — proxy `/openapi.json` to the backend like `/api`.

## Data Contracts

None new. Reads the OpenAPI 3.1 document produced by FastAPI.

## Interfaces / Contracts

No new endpoints. Scenario requests use (all under `/api/v1`):

| Scenario | Requests |
| -------- | -------- |
| Schedule lifecycle | `GET /initiatives`, `GET /workflow-definitions`, `GET /workflow-definitions/{id}`, `POST /schedules/preview`, `POST /schedules`, `GET /schedules/{id}`, `POST …/trigger`, `GET …/runs`, `POST …/pause`, `POST …/resume`, `POST …/archive` |
| Activity Definition | `POST /activity-definitions`, `POST …/{id}/render`, `GET …/{id}`, `DELETE …/{id}` |
| Story execution | `GET /initiatives`, `POST /stories`, `POST /stories/{id}/start`, `GET /executions/{id}`, `GET …/timeline`, `GET …/decisions` |
| Workflow Definition | `POST /workflow-definitions`, `GET …/{id}`, `PATCH …/{id}`, `DELETE …/{id}` |

## Test Plan

The frontend has no unit-test runner (testing.md §2: typecheck + build is the
frontend gate). Verification:

| AC | How |
| -- | --- |
| AC-1, AC-2, AC-3, AC-4, AC-5, AC-9, AC-10 | Manual run of the console against `uv run uvicorn …` (scenarios listed in spec). |
| AC-6, AC-7, AC-8 | Backend test `backend/tests/test_api_console_scenarios.py` replays the same request sequences against the app (`TestClient`), so the backend side of each scenario is guarded in CI; plus manual run in the console. |
| all | `npm run typecheck && npm run build`. |

## Alternatives Considered

- **Hand-written forms per endpoint** — rejected: drifts from the contract and
  multiplies UI code.
- **Link to Swagger (`/api`)** — already exists, but has no scenarios, no id
  reuse, and no realtime log.
- **Go through `ApiClient`** — rejected: covers only methods the UI needs and
  follows the mock flag.

## Risks & Mitigations

- Scenario breaks when the API changes → the backend replay test fails first.
- Scenarios leave data behind on failure → only on failure, and the failing
  step is shown; catalog data is cleaned up on success.

## Rollout / Sequencing

Single slice: explorer + scenarios + event log behind the `/console` route.
