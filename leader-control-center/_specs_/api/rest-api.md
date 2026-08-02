# REST API

The API exposes **business commands** instead of CRUD. The backend translates
these into workflow-engine operations. Contract is published via OpenAPI.

Base path: `/api/v1`

---

## Philosophy

- Commands express intent (`POST /tasks/{id}/start`), not table mutations.
- Queries return projections (read models), never raw aggregates.
- Workflow engines remain hidden behind the backend.

---

## Planning

```
POST   /initiatives                 create Initiative { title, description }
POST   /initiatives/reorder         reorder initiatives { initiativeIds: [...] }
POST   /initiatives/{id}/epics      create Epic
POST   /stories                     create Story { epicId, title, description?, priority?, acceptanceCriteria? }
POST   /stories/draft               draft Story fields from natural language (LLM-assisted prefill)
POST   /tasks                       create Task (Structured or Goal-Oriented)
PATCH  /stories/{id}                update Story
PATCH  /tasks/{id}                  update Task
POST   /tasks/{id}/ready            mark Task Ready
POST   /tasks/{id}/cancel           cancel Task (planning)
```

Task creation body selects the planning mode:

```jsonc
// Structured
{ "storyId": "...", "name": "...", "planningMode": "Structured",
  "capabilityId": "...", "dependencies": [], "acceptanceCriteria": [] }

// Goal-Oriented (future)
{ "storyId": "...", "name": "...", "planningMode": "GoalOriented",
  "goal": "...", "successCriteria": [] }
```

---

## Execution

```
POST   /stories/{id}/start          create + start Story Execution
POST   /tasks/{id}/start            create + start Task Execution
POST   /executions/{id}/cancel      cancel a running execution
POST   /executions/{id}/retry       retry (new execution instance)
```

---

## Decisions

A **decision to make** is an open request for human input on an execution
(surfaced in the UI via the Attention Queue). List the open decisions for an
execution, then apply exactly one action per decision.

```
GET    /executions/{id}/decisions                          open decisions (each with its available actions)
POST   /executions/{id}/decisions/{decisionId}/approve
POST   /executions/{id}/decisions/{decisionId}/reject      { "comment": "..." }
POST   /executions/{id}/decisions/{decisionId}/clarify     { "message": "..." }
POST   /executions/{id}/decisions/{decisionId}/continue
POST   /executions/{id}/decisions/{decisionId}/abort
POST   /executions/{id}/decisions/{decisionId}/retry
POST   /executions/{id}/decisions/{decisionId}/select      { "optionId": "..." }
POST   /executions/{id}/decisions/{decisionId}/custom      { "actionName": "...", ... }
```

- `GET /executions/{id}/decisions` returns each open decision together with the
  set of actions it accepts (its choice enum), so the client renders the right
  controls.
- The action segment is one of the standard decision kinds (`approve`,
  `reject`, `clarify`, `continue`, `abort`, `retry`, `select`) or `custom` with
  an explicit `actionName` for extensible, non-standard actions.
- Each action resolves the decision via a workflow signal and records an
  immutable Decision.

---

## Runtime Queries

```
GET    /initiatives                 list initiative summaries (order + counts)
GET    /initiatives/{id}/board      per-initiative Kanban view
GET    /executions                  list executions (filterable)
GET    /executions/{id}             execution detail + live status
GET    /executions/{id}/timeline    append-only timeline
GET    /stories/{id}/artifacts      artifacts (latest versions)
GET    /artifacts/{id}              artifact detail + versions
GET    /attention                   Attention Queue (cross-initiative)
```

> **Terminology.** `Execution` is the API/runtime term; the UI labels it a
> **Story**. `GET /executions` returns all executions, and an execution's
> timeline and decisions live under `/executions/{id}`.

> **Board.** `GET /initiatives` returns lightweight summaries — each carries the
> `Initiative` (including its `order`), its `epicId`, a `storyCount`, and the
> `openHumanRequests` count — so the board list renders (and shows badges) with
> every initiative collapsed by default. Unfolding an initiative loads its Kanban
> columns on demand via `GET /initiatives/{id}/board`. Initiatives are returned
> in ascending `order`; drag-to-reorder persists the new order atomically via
> `POST /initiatives/reorder` (`{ initiativeIds: [...] }`, order = list index).

> **Create Story.** The Todo column of each board ends with an add-story card (a
> centered `+`) that opens a right-hand drawer scoped to that initiative's epic.
> The drawer has a form on top (title `*` required; description, priority, and
> acceptance criteria optional) and a chat box at the bottom. Typing intent into
> the chat and pressing Send calls `POST /stories/draft` (`{ initiativeId,
> message }`), which returns prefilled fields (`{ title, description, priority,
> acceptanceCriteria }`) the user can review and edit. This is an LLM-assisted
> step; until an LLM provider is wired it is served by a deterministic heuristic
> stub. Pressing Create submits `POST /stories`, which creates the Story with
> planning status `Draft` (landing it in the Todo column) and returns it.

---

## Catalog

```
GET    /capabilities                Capability Catalog
GET    /capabilities/{id}
GET    /providers                   configured Providers
```

---

## Notifications

A Notification is created when a decision is made; it carries the decision
reference (ids, choices, links) and has its own lifecycle.

```
GET    /notifications               open notifications, ordered by status (UNREAD, then READ, then ACKED), each ascending by time
POST   /notifications/{id}/open     UNREAD -> READ
POST   /notifications/{id}/ack      READ   -> ACKED
POST   /notifications/{id}/close    ACKED  -> CLOSED
```

Status lifecycle:

```
UNREAD --open--> READ --ack--> ACKED --close--> CLOSED
```

- `UNREAD`, `READ`, `ACKED` are open states; `CLOSED` is terminal (the
  referenced action is complete).
- `GET /notifications` returns only open notifications (excludes `CLOSED`).

---

## Conventions

### Resource envelope
Every resource exposes:
```
id · version · createdAt · updatedAt
```

### Optimistic locking
Mutating requests send `If-Match: <version>`; a stale version returns `409
Conflict`. See [../backend/services-and-commands.md](../backend/services-and-commands.md).

### Idempotency
Start/Retry accept an `Idempotency-Key` header.

### Errors
Problem+JSON style: `{ type, title, status, detail, instance }`.

### Status codes
`200` ok · `201` created · `202` accepted (async execution) · `400` validation ·
`401/403` auth · `404` not found · `409` conflict · `422` invariant violation.

---

## Realtime

Live updates are delivered over WebSocket (see [realtime.md](./realtime.md)); the
REST API is for commands and initial/loading queries.
