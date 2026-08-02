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
POST   /initiatives                 create Initiative
POST   /initiatives/{id}/epics      create Epic
POST   /stories                     create Story
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
GET    /initiatives                 list initiatives (board summary)
GET    /initiatives/{id}/board      Kanban view
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

> **Board (MVP status).** The target shape is `GET /initiatives` (list) +
> `GET /initiatives/{id}/board` (per-initiative Kanban). The MVP currently
> serves the full board projection directly from `GET /initiatives`;
> `/initiatives/{id}/board` is kept as the target but not yet implemented.

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
