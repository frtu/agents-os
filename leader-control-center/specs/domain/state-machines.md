# State Machines

Every planning and runtime entity has an explicit lifecycle. These are the
authoritative state sets; the API, database, and UI must not invent states
outside them.

> Planning states change slowly. Runtime states change constantly.

---

## Planning Lifecycle (generic)

Applies to Epic, Story, and Planning as a whole.

```
Draft → Ready → Archived
```

- **Draft** — under construction; not executable.
- **Ready** — approved for execution.
- **Archived** — retired; retained for history.

---

## Task (planning state)

```
Draft → Ready → Cancelled
```

- Only a **Ready** Task may be started.
- Planning state is distinct from execution state (below). Cancelling a Task
  stops future scheduling; it does not alter past executions.

> Note: the board columns (Todo / Ready / Running / Blocked / Completed) are a
> **UI projection** that combines a Task's planning state with the status of its
> latest Task Execution. They are not stored planning states. See
> [../frontend/frontend.md](../frontend/frontend.md).

---

## Story Execution

```
Created → Running → Waiting → Completed
                 ↘         ↗
                  Cancelled
                  Failed
```

- **Created** — instantiated, not yet running.
- **Running** — orchestrating Task Executions.
- **Waiting** — blocked on a Human Request.
- **Completed / Cancelled / Failed** — terminal.

---

## Task Execution

```
Created → Running → WaitingDecision → Running → Completed
                                             ↘
                                              Failed
                                              Cancelled
```

- Enters **WaitingDecision** when a Human Request is raised; returns to
  **Running** once the Decision is applied.
- **Completed / Failed / Cancelled** — terminal.

---

## Capability Execution

```
Pending → Running → Waiting → Completed
                          ↘
                           Failed
```

- **Pending** — strategy selected, providers not yet scheduled.
- **Running** — one or more Provider Executions active.
- **Waiting** — awaiting a Human Request (e.g. Human Review strategy).
- **Completed / Failed** — terminal, decided by the Execution Strategy.

---

## Provider Execution

```
Scheduled → Running → Succeeded
                   ↘
                    Failed
                    Cancelled
```

- A **Failed** Provider Execution does **not** imply Capability failure — the
  Execution Strategy determines retry, failover, consensus, or human
  intervention. See [../execution/execution-strategy.md](../execution/execution-strategy.md).

---

## Human Request

```
Created → Visible → Acknowledged → Resolved → Closed
```

- **Visible** — surfaced in the Attention Queue.
- **Acknowledged** — a user has opened it.
- **Resolved** — a Decision has been submitted.
- **Closed** — the Decision has been applied to the execution.

---

## Decision

```
Requested → Viewed → Responded → Applied → Closed
```

- One Decision corresponds to exactly one Human Request.
- Once **Applied**, a Decision is immutable.

---

## Artifact

```
Draft → Published → (new version → Draft → Published …)
```

- Artifacts are immutable once **Published**; changes create a new version.
- Optional review gate: `Published → UnderReview → Approved | Rejected`
  (Rejected produces a Human Request, not a mutation).

---

## Transition Rules Summary

| From context | Trigger | Effect |
| ------------ | ------- | ------ |
| Task `Ready` | `StartTask` command | creates Task Execution (`Created`) |
| Task Execution `Running` | raises Human Request | → `WaitingDecision` |
| Human Request `Resolved` | Decision applied | Task Execution → `Running` |
| Provider Execution `Failed` | strategy = Retry | new Provider Execution `Scheduled` |
| Story Execution all tasks terminal | aggregation | → `Completed` / `Failed` |

Every transition emits an immutable Timeline event — see
[event-model.md](./event-model.md).
