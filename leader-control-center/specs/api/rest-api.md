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

```
POST   /executions/{id}/approve
POST   /executions/{id}/reject
POST   /executions/{id}/clarify     { "message": "..." }
POST   /executions/{id}/continue
POST   /executions/{id}/abort
POST   /executions/{id}/select      { "optionId": "..." }
```

Each resolves the execution's open Human Request via a workflow signal.

---

## Runtime Queries

```
GET    /initiatives                 list initiatives (board summary)
GET    /initiatives/{id}/board      Kanban view
GET    /executions                  list executions (filterable)
GET    /executions/{id}             execution detail + live status
GET    /stories/{id}/timeline       append-only timeline
GET    /stories/{id}/artifacts      artifacts (latest versions)
GET    /artifacts/{id}              artifact detail + versions
GET    /attention                   Attention Queue (cross-initiative)
```

---

## Catalog

```
GET    /capabilities                Capability Catalog
GET    /capabilities/{id}
GET    /providers                   configured Providers
```

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
