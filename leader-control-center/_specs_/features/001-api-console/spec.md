# Feature Specification: API Console

**Feature ID:** `001-api-console`
**Status:** Draft
**Created:** 2026-10-04 · **Last Updated:** 2026-10-04

**Amends:** [frontend/frontend.md](../../frontend/frontend.md) (Navigation, Views → API Console)

## Summary

A developer-facing **API Console** page in the frontend, for checking backend
behaviour quickly without curl or Swagger: browse every endpoint, send a request
with a prefilled body, read the response, and run one-click **scenarios** that
chain commands end to end (e.g. create a Schedule → trigger it → read its runs).
A live log shows the realtime events the backend emits while you work. It is a
test bench for people building the Control Center, not a leader-facing view.

## Goals

- Reach **every** backend endpoint from one page, with no per-endpoint UI to
  maintain (the endpoint list follows the backend contract automatically).
- Make the common checks one click: Schedules, Tasks (Activity Definitions),
  Story execution, Workflow Definitions.
- Show exactly what happened: status, duration, response body, and the backend's
  error detail on failure.
- Show the realtime events produced by each action.

## Non-Goals

- Not a leader-facing feature; it does not replace the Board, Schedules, or Tasks
  pages and adds no business capability.
- No new backend endpoints and no change to the wire contract.
- No authentication, saved collections, or request sharing.
- Does not exercise the in-browser mock backend; the console always targets the
  real backend.

## User Scenarios

- **Scenario 1 — Browse & send:** As a developer, I open *Console*, filter for
  `schedules`, pick `POST /schedules/preview`, see a body prefilled with valid
  example values, edit it, press Send, and see `200`, the duration, and the JSON
  response.
- **Scenario 2 — Reuse ids:** After listing initiatives, the ids in the response
  are offered as suggestions when I fill `{initiative_id}` on the next request.
- **Scenario 3 — Check schedules:** I run the *Schedule lifecycle* scenario; it
  previews, creates, triggers, reads runs, pauses, resumes, and archives a
  Schedule, showing each step as passed or failed with its response.
- **Scenario 4 — Check tasks:** I run the *Activity Definition* scenario; it
  creates a temporary bash definition, renders it with parameters, reads it back,
  and deletes it.
- **Scenario 5 — Check a story run:** I run the *Story execution* scenario; it
  creates a Story, starts it, reads the execution, timeline, and open decisions.
- **Scenario 6 — See events:** While a scenario runs, the event log shows the
  `ScheduleUpdated` / `ScheduleRunRecorded` / `ExecutionUpdated` messages it
  caused.
- **Scenario 7 — Failure is explicit:** A request the backend rejects shows its
  status and Problem+JSON `detail`; a failed scenario step stops the scenario and
  names the step and reason.

## Functional Requirements

### Endpoint explorer

- **FR-1:** The console MUST list every operation the backend publishes in its
  OpenAPI document, grouped by tag, with a text filter over method, path, and
  summary.
- **FR-2:** For a selected operation the console MUST provide inputs for each path
  and query parameter and, when the operation accepts a JSON body, a body editor
  prefilled with an example built from the request schema (required fields,
  defaults, first enum value).
- **FR-3:** Sending MUST show the HTTP status, duration in ms, and the response
  body (pretty-printed JSON, or raw text).
- **FR-4:** If the body editor holds invalid JSON, the console MUST NOT send and
  MUST say why.
- **FR-5:** Ids found in responses (`id` and `…Id` fields) MUST be remembered for
  the session and offered as suggestions for path parameters.
- **FR-6:** Every request MUST be recorded in a session history (method, path,
  status, duration); selecting an entry MUST show its request and response again.

### Scenarios

- **FR-7:** The console MUST offer scenarios that run a fixed sequence of
  requests, each step showing its request, status, and response, and pass/fail.
- **FR-8:** Provided scenarios: **Schedule lifecycle** (preview → create →
  get → trigger → runs → pause → resume → archive), **Activity Definition**
  (create bash → render → get → delete), **Story execution** (create Story →
  start → get execution → timeline → open decisions), **Workflow Definition**
  (create → get → update → delete).
- **FR-9:** Scenarios MUST derive their inputs from the current backend state
  (first initiative and its epic, first Workflow Definition and its input
  schema), not from hard-coded ids.
- **FR-10:** A failed step MUST stop the scenario and show the step name, status,
  and the backend's error detail (constitution P9).
- **FR-11:** Scenarios that create catalog data (Activity / Workflow Definition,
  Schedule) MUST clean up after themselves on success (delete or archive).
  Planning objects (Stories) remain, as planning history is permanent (P2).

### Realtime

- **FR-12:** The console MUST show a live, newest-first log of realtime messages
  (type, aggregate id, sequence, time), with a clear button.

### Access

- **FR-13:** The console MUST be reachable from the sidebar as **Console** at
  `/console`.
- **FR-14:** If the OpenAPI document cannot be loaded, the console MUST say so,
  including the reason and the URL it tried, and scenarios MUST still be
  available.

## Key Entities & Concepts

- **Operation** — one method + path from the backend contract.
- **Scenario** — a named, ordered list of steps; each step is one request whose
  inputs may use the results of earlier steps.
- **Step result** — status, duration, request, response, pass/fail.

## Constraints & Assumptions

- Uses only existing endpoints (constitution P3); engine internals are never
  shown because the API does not expose them (P4).
- Assumes the backend publishes its OpenAPI document (FastAPI default).
- Runs against the real backend even when the rest of the UI uses mocks.

## Acceptance Criteria

- [ ] AC-1 Every operation in the backend OpenAPI document appears in the
  explorer, grouped by tag, and the filter narrows the list. (FR-1)
- [ ] AC-2 Selecting `POST /schedules/preview` prefills a body that the backend
  accepts after filling `initiativeId`. (FR-2, FR-3)
- [ ] AC-3 Invalid JSON is blocked with a message; a 404 shows the Problem+JSON
  detail. (FR-4, FR-3)
- [ ] AC-4 Ids from a response are suggested for the next path parameter. (FR-5)
- [ ] AC-5 History lists each request and re-displays it on selection. (FR-6)
- [ ] AC-6 Each of the four scenarios passes against a freshly seeded backend.
  (FR-7, FR-8, FR-9)
- [ ] AC-7 A failing step stops its scenario and shows status + detail. (FR-10)
- [ ] AC-8 After a passing scenario, no temporary Activity / Workflow Definition
  remains and the scenario's Schedule is Archived. (FR-11)
- [ ] AC-9 Running the Schedule scenario adds Schedule messages to the event log.
  (FR-12)
- [ ] AC-10 The sidebar shows Console; with the backend down the page explains
  why the endpoint list is missing. (FR-13, FR-14)

## Open Questions

- None.

## Review Checklist

- [x] No implementation details (how) leaked into this spec.
- [x] Every requirement is testable and has an id.
- [x] Scenarios cover the golden path and key edge cases.
- [x] Complies with [`constitution.md`](../../constitution.md).
- [x] Every amended area spec is listed under **Amends**.
