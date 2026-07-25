# /specs/backend-api.md

# Backend API

## Philosophy

Business Commands instead of CRUD.

---

# Planning

POST /epics

POST /stories

POST /tasks

PATCH /stories/{id}

PATCH /tasks/{id}

---

# Execution

POST /tasks/{id}/start

POST /tasks/{id}/cancel

POST /tasks/{id}/retry

---

# Decisions

POST /executions/{id}/approve

POST /executions/{id}/reject

POST /executions/{id}/clarify

POST /executions/{id}/continue

POST /executions/{id}/abort

---

# Runtime

GET /executions

GET /executions/{id}

GET /stories/{id}/timeline

GET /stories/{id}/artifacts

GET /attention

---

# Events

Realtime updates use WebSocket.

Future fallback

Server Sent Events.

Examples

```
StoryUpdated

ExecutionUpdated

TimelineUpdated

DecisionRequested

ArtifactProduced

NotificationCreated
```

Clients maintain synchronized local state.

---

# Versioning

Every resource exposes:

id

version

updatedAt

createdAt

optimistic locking version
