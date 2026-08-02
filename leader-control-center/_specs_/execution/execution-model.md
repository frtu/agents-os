# Execution Model

Planning objects describe **intent**. Execution objects describe **runtime**. The
same Task may execute many times without modifying planning.

```
Task
 ├── Execution #1 (Failed)
 ├── Execution #2 (Cancelled)
 └── Execution #3 (Completed)
```

> Planning is immutable. Runtime is disposable. History is permanent.

---

## Execution Hierarchy

```
Story Execution
 └── Task Execution
      └── Capability Execution
           ├── Provider Execution
           ├── Provider Execution
           └── Provider Execution
```

Each level owns exactly one responsibility.

---

## Story Execution

One runtime instance of a Story.

**Responsibilities**
- orchestrate Task Executions (per the active Scheduling Strategy)
- aggregate status and progress
- aggregate Artifacts
- surface Human Requests
- expose the Story Timeline

Story Execution **orchestrates**; it never performs work.
Lifecycle: `Created → Running → Waiting → Completed | Cancelled | Failed`.

---

## Task Execution

One runtime instance of a Task.

**Responsibilities**
- resolve the Task's Capability (Structured) or planner output (Goal-Oriented)
- run the Capability via an Execution Strategy
- request human interaction (Human Requests)
- produce Artifacts
- publish runtime events

Lifecycle: `Created → Running → WaitingDecision → Running → Completed | Failed | Cancelled`.

---

## Capability Execution

Represents **what ability is required**. Runs exactly one **Execution Strategy**,
which decides how Providers are invoked.

**Responsibilities**
- select and run the Execution Strategy
- coordinate one or more Provider Executions
- decide success/failure based on strategy semantics

Lifecycle: `Pending → Running → Waiting → Completed | Failed`.
See [execution-strategy.md](./execution-strategy.md).

---

## Provider Execution

The concrete run against one **Provider**.

**Responsibilities**
- invoke a Provider through its contract (`execute`, `cancel`, `resume`)
- stream progress and intermediate output
- report success/failure

Lifecycle: `Scheduled → Running → Succeeded | Failed | Cancelled`.

A Provider failure does **not** necessarily imply a Capability failure — the
Execution Strategy determines whether retries, failover, consensus, or human
intervention occur. See [providers.md](./providers.md).

---

## Retry Policy

Retries always create a **new** Execution; planning is never modified.

```
Task → Execution 1 → Failed → Retry → Execution 2
```

Previous executions remain available for audit.

---

## Cancellation

Cancelling an execution never deletes history. Status becomes `Cancelled`; the
Timeline remains intact.

---

## Completion

A Task Execution completes when:
- its Capability Execution reports `Completed`, and
- any required Artifacts are produced, and
- any required Decisions are applied.

A Story advances only when its Task Executions reach terminal states satisfying
the Story's Acceptance Criteria.

---

## Normalization from Planning Modes

Both Structured and Goal-Oriented Tasks produce the identical runtime shape:

| Planning input | Runtime resolution |
| -------------- | ------------------ |
| Structured Task (capability fixed) | Capability Execution with that Capability |
| Goal-Oriented Task (goal) | AI Planner derives Capabilities → same Capability Executions |

See [../planning/planning-modes.md](../planning/planning-modes.md).

---

## Invariants

1. Runtime never mutates planning.
2. Every retry/cancel produces new immutable history, never edits old history.
3. A Capability Execution runs exactly one Execution Strategy.
4. Provider selection happens only inside a Capability Execution, at runtime.
