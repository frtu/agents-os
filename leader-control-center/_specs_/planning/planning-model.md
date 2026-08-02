# Planning Model

Planning is the internal representation of an Initiative. It defines **what**
should happen and remains **stable** throughout execution.

```
Initiative → Epic → Story → Task → Ready
```

> Planning is immutable intent. It is never modified by runtime.

---

## Hierarchy

### Initiative
The business outcome the leader supervises. Backed by one or more Epics. Leaders
plan, launch, and monitor at the Initiative level.

### Epic
Primary planning container grouping Stories toward one Initiative. Scoped to
~one month of work. Lifecycle: `Draft → Ready → Archived`.

### Story
A business deliverable. Owns Tasks, Dependencies, and Acceptance Criteria.
Progresses across the planning board.

### Task
A unit of planned work describing **what** to accomplish. Created in exactly one
**Planning Mode** (see [planning-modes.md](./planning-modes.md)). Planning
lifecycle: `Draft → Ready → Cancelled`. Only **Ready** Tasks may be started.

---

## Task Definition

A Structured Task carries:

```
Task {
  id
  storyId
  name
  planningMode = "Structured"
  capabilityId          # from the Capability Catalog
  dependencies[]        # Task IDs
  acceptanceCriteria[]
  status                # Draft | Ready | Cancelled
  order
}
```

A Goal-Oriented Task carries:

```
Task {
  id
  storyId
  name
  planningMode = "GoalOriented"
  goal                  # natural-language desired outcome
  successCriteria[]
  dependencies[]
  status
  order
}
```

Both normalize into the same execution model at runtime — see
[../execution/execution-model.md](../execution/execution-model.md).

---

## Dependencies

A Dependency is a prerequisite relationship between Tasks.

```
Dependency { taskId, dependsOnTaskId }
```

- **MVP:** informational only (documented, shown in UI).
- **Future:** consumed by Dependency Scheduling to auto-start Tasks when
  prerequisites complete. See [scheduling.md](./scheduling.md).

Dependencies must form a DAG (no cycles).

---

## Acceptance Criteria

Define completion conditions for a Story (and optionally a Task).

```
AcceptanceCriteria { id, storyId | taskId, description }
```

Example:

```
Story: Write Promotion Document
- Executive quality
- Less than three pages
- Ready for manager review
```

Acceptance Criteria inform Human Review strategies and Story completion (see
[../execution/execution-model.md](../execution/execution-model.md#completion)).

---

## Planning Workflow

```
Draft   →  author Epics/Stories/Tasks
  ↓
Ready   →  approved; eligible for execution
  ↓
Executing (runtime; planning unchanged)
  ↓
Archived → retired, retained for history
```

Planning remains stable while runtime evolves. Retrying or restarting an
execution never changes planning.

---

## Invariants

1. A Task belongs to exactly one Story; a Story to exactly one Epic; an Epic to
   exactly one Initiative.
2. A Task has exactly one Planning Mode.
3. A Structured Task references a Capability that exists in the Catalog.
4. Dependencies reference Tasks within the same Story (MVP) and form a DAG.
5. Only **Ready** Tasks may be started.
6. Planning entities are never mutated by runtime events.
