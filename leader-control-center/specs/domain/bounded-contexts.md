# Bounded Contexts

The system is partitioned into bounded contexts that communicate through
**commands** and **events** — never by sharing mutable state. This keeps
Planning stable while Runtime evolves independently.

---

## Context Map

```
┌──────────────┐   commands   ┌──────────────┐   commands   ┌──────────────┐
│   Planning   │ ───────────▶ │   Runtime    │ ───────────▶ │  Workflow    │
│   Context    │              │   Context    │              │  Engine      │
│              │ ◀─────────── │              │ ◀─────────── │  Context     │
└──────────────┘    events    └──────────────┘    events    └──────────────┘
        │                            │                             
        │ reads catalog              │ resolves                    
        ▼                            ▼                             
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│   Catalog    │              │  Attention   │              │  Identity &  │
│   Context    │              │  Context     │              │  Access      │
└──────────────┘              └──────────────┘              └──────────────┘
```

---

## 1. Planning Context

**Owns:** Portfolio, Initiative, Epic, Story, Task, Dependency, Acceptance
Criteria.

**Aggregate roots:**
- **Initiative** — consistency boundary for its Epics/Stories/Tasks planning.
- **Portfolio** — consistency boundary for org-level settings.

**Responsibilities:** define and maintain immutable intent; expose planning
state (`Draft → Ready → Archived`).

**Never:** references runtime IDs; depends on execution status.

---

## 2. Runtime Context

**Owns:** Story Execution, Task Execution, Capability Execution, Provider
Execution, Human Request, Decision, Artifact, Timeline, Metrics.

**Aggregate roots:**
- **Story Execution** — consistency boundary for its Task Executions and their
  child executions, timeline, and human requests.

**Responsibilities:** orchestrate execution, request human interaction, produce
artifacts, emit events.

**Reads (never writes):** Planning (to instantiate executions) and Catalog (to
resolve capabilities/providers).

---

## 3. Catalog Context

**Owns:** Capability, Capability Catalog, Provider, Provider credentials/config,
Execution Strategy definitions.

**Responsibilities:** provide the reusable, provider-independent set of
capabilities and the interchangeable providers that implement them.

**Scope:** Portfolio/Workspace level; shared across all Initiatives.

---

## 4. Workflow Engine Context

**Owns:** the adapter to durable workflow engines (Temporal first).

**Responsibilities:** translate Runtime commands into workflow operations
(start/signal/query/cancel); surface engine events back as domain events.

**Boundary rule:** engine concepts (WorkflowId, RunId, Activity) never leak past
this context. See [../workflow-engine/workflow-engine.md](../workflow-engine/workflow-engine.md).

---

## 5. Attention Context

**Owns:** the Attention Queue read model.

**Responsibilities:** aggregate open Human Requests and failures across all
Initiatives, sorted by priority and waiting time. Pure projection over Runtime
events. See [../execution/human-requests.md](../execution/human-requests.md).

---

## 6. Identity & Access Context

**Owns:** Users, authentication, authorization/permissions.

**Responsibilities:** who may start executions, approve decisions, cancel
workflows. See [../auth/auth.md](../auth/auth.md) and
[../permissions/permissions.md](../permissions/permissions.md).

---

## Integration Rules

1. Contexts integrate via **commands** (intent) and **events** (facts) only.
2. Planning → Runtime is **one-directional**: Planning emits intent; Runtime
   never writes back to Planning.
3. Catalog is **read-only** from the perspective of Planning and Runtime.
4. All cross-context IDs are references, not embedded aggregates.
5. Read models (Timeline, Attention Queue, Metrics) are projections and never the
   source of truth. See [event-model.md](./event-model.md).
