# Scheduling Strategy

The application separates **scheduling policy** (when a Task starts) from
**execution** (how a Capability runs). Scheduling strategies evolve without
changing the workflow hierarchy.

```
Story Workflow
  ↓
Scheduling Strategy
  ├── Manual Scheduling      (MVP)
  ├── Dependency Scheduling  (future)
  └── AI Planning            (future)
```

---

## Manual Scheduling (MVP)

The leader explicitly starts every Task.

```
Leader → Start Task → Backend → Workflow Engine
```

- No automatic transitions between Tasks.
- Dependencies are shown but not enforced.
- Maximum human control; the baseline all other strategies build on.

---

## Dependency Scheduling (future)

Tasks automatically start when their dependencies are satisfied.

- Consumes the Dependency DAG from [planning-model.md](./planning-model.md).
- The leader sets the Story running; the scheduler advances Ready Tasks whose
  prerequisites have completed.
- Still human-supervised: Human Requests pause the chain.

---

## AI Planning (future)

The AI dynamically creates, reprioritizes, and launches Tasks.

- Operates within an Initiative's guardrails.
- Emits explicit Tasks/Capabilities so runtime and audit remain inspectable.
- Plans remain **Draft** until approved unless the Portfolio enables autonomous
  mode.

---

## Contract

All strategies implement a common policy interface so the Story Workflow is
agnostic to which one is active:

```
SchedulingStrategy
  selectNextTasks(story, runtimeState) → [taskId]
  onTaskCompleted(taskId, runtimeState) → [taskId]   # may return next tasks
```

- **Manual:** `selectNextTasks` returns only tasks the leader explicitly started.
- **Dependency:** returns Ready tasks whose dependencies are complete.
- **AI Planning:** returns tasks proposed/launched by the planner.

---

## Invariants

1. Changing the Scheduling Strategy never changes the workflow hierarchy
   (Story → Task → Capability → Provider).
2. A strategy may only start **Ready** Tasks.
3. Human Requests always take precedence over automatic scheduling — the chain
   pauses until a Decision is applied.

See the autonomy roadmap in [../overview/roadmap.md](../overview/roadmap.md).
