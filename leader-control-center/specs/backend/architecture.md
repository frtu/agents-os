# Backend Architecture

The backend owns the business model and is the single source of truth. Workflow
engines own execution. The frontend never communicates directly with workflow
engines.

---

## Layered Architecture

```
                React Frontend
                      │
              REST + WebSocket
                      │
────────────────────────────────────────
             Backend API Layer            # command/query endpoints
────────────────────────────────────────
     Application Services / Commands       # use cases, orchestration
────────────────────────────────────────
   Domain Model (Planning + Runtime)       # aggregates, invariants, events
────────────────────────────────────────
          Workflow Management Layer        # scheduling + execution strategies
────────────────────────────────────────
          Workflow Engine Adapter (port)   # translate to engine ops
────────────────────────────────────────
        Temporal            Future Engines
```

- The UI never talks to workflow engines.
- The workflow engine never owns planning.
- The backend is the single source of truth.

---

## Architectural Principles

### Planning and Runtime are separate bounded contexts
They communicate via commands and events only. Planning changes slowly; runtime
changes constantly. See [../domain/bounded-contexts.md](../domain/bounded-contexts.md).

### Business model is workflow-agnostic
The backend exposes domain objects (StoryExecution, Timeline, Decision), never
Temporal concepts (WorkflowId, RunId, Activity).

### Everything is command-driven
Clients never mutate state directly; they send Commands. Commands produce Events;
Events update Read Models.

```
Command → Event → Read Model
```

### Event-driven runtime
Runtime state is projected from immutable events, giving auditability, replay,
debugging, and analytics. See [../domain/event-model.md](../domain/event-model.md).

### Ports & Adapters
Business logic depends only on interfaces (WorkflowEngine, Provider,
SchedulingStrategy, ExecutionStrategy). Concrete engines/providers are adapters.

---

## CQRS & Event Sourcing (pragmatic)

- **Write side:** commands validated against aggregates emit events (source of
  truth).
- **Read side:** projections (Timeline, Attention Queue, Kanban, Metrics) built
  from events, optimized for query.
- **MVP pragmatism:** event sourcing is applied to the **Runtime** context
  (executions, timeline). The **Planning** context may use straightforward
  persisted aggregates with events emitted for projections. Full event sourcing
  of Planning is optional and deferred.

---

## Technology Stack

**Backend**
- Python
- FastAPI
- OpenAPI (generated contract)
- PostgreSQL

**Workflow**
- Temporal (initial target)
- Additional engines via adapters (future)

See [../database/data-model.md](../database/data-model.md),
[../api/rest-api.md](../api/rest-api.md), and
[../workflow-engine/workflow-engine.md](../workflow-engine/workflow-engine.md).

---

## Module Boundaries (suggested)

```
app/
  api/            # FastAPI routers (commands + queries)
  application/    # use cases / command handlers
  domain/
    planning/     # Initiative, Epic, Story, Task aggregates
    runtime/      # executions, human requests, artifacts, timeline
    catalog/      # capabilities, providers
  workflow/       # WorkflowEngine port + Temporal adapter
  strategies/     # scheduling + execution strategies
  projections/    # read models
  infra/          # persistence, messaging, secrets
```

Dependencies point inward: `api → application → domain`; adapters depend on
domain ports, never the reverse.
