# Human Requests, Decisions & Attention Queue

The platform pauses execution **only** through Human Requests. This is how the
Human First principle is enforced at runtime.

---

## Human Request

A first-class runtime object representing something requiring human attention.

```
HumanRequest {
  id
  executionId          # task/capability execution that raised it
  initiativeId
  type
  prompt               # what the human is being asked
  options[]            # for Choose Option
  status               # Created | Visible | Acknowledged | Resolved | Closed
  priority
  createdAt
}
```

### Types

- Approval
- Clarification
- Budget
- Tool Permission
- Missing Information
- Choose Option
- Risk Acceptance

Lifecycle: `Created → Visible → Acknowledged → Resolved → Closed` (see
[../domain/state-machines.md](../domain/state-machines.md)).

---

## Decision

Every Human Request produces exactly one Decision — the immutable human response.

```
Decision {
  id
  humanRequestId
  decision             # Approve | Reject | Clarify | Continue | Abort | Retry | SelectOption
  selectedOption       # for SelectOption
  comment
  user
  createdAt
}
```

- Workflows wait for **Decisions**, not for bare approvals.
- Once applied, a Decision is immutable and fully auditable (user, timestamp,
  execution, reason).

Lifecycle: `Requested → Viewed → Responded → Applied → Closed`.

---

## Request → Decision Flow

```
Execution raises HumanRequest
   ↓  (Task/Story Execution → Waiting)
Surfaced in Attention Queue
   ↓
User acknowledges & submits Decision
   ↓
Decision applied as a workflow signal
   ↓
Execution resumes (Running) or terminates (Abort)
```

Applying a Decision is delivered to the workflow engine as a **signal** — see
[../workflow-engine/workflow-engine.md](../workflow-engine/workflow-engine.md).

---

## Attention Queue

A cross-Initiative read model aggregating everything needing human attention, so
leaders supervise many concurrent workflows without constant interruption.

**Includes**
- Waiting approvals
- Waiting clarification
- Execution failures
- Tool permission requests
- Budget approvals

**Sort keys:** priority, waiting time, Initiative, execution.

The Attention Queue is a pure projection over Runtime events (Attention context,
see [../domain/bounded-contexts.md](../domain/bounded-contexts.md)); it owns no
source-of-truth state.

---

## Human Request vs Notification

| | Human Request | Notification |
| - | ------------- | ------------ |
| Blocks execution | Yes | No |
| Requires a Decision | Yes | No |
| Appears in | Attention Queue | Notifications |

See [../notifications/notifications.md](../notifications/notifications.md).

---

## Invariants

1. Execution pauses only via a Human Request.
2. Exactly one Decision resolves one Human Request.
3. Decisions are immutable and traceable to user + timestamp + execution + reason.
4. The Attention Queue never mutates runtime state; it only projects it.
