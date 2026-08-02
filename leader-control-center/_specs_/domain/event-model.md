# Event Model

Everything that happens produces an **immutable, append-only event**. Events are
the source of truth; all read models (Timeline, Attention Queue, Metrics,
Analytics) are projections built from them.

```
Command → Event → Read Model
```

No consumer owns the source of truth.

---

## Event Envelope

Every event shares a common envelope:

```
Event {
  id            # unique event id
  type          # e.g. "TaskStarted"
  category      # Planning | Runtime | Decision | Artifact | Notification | System
  aggregateId   # the entity the event belongs to
  initiativeId  # for cross-initiative projections
  payload       # type-specific data
  actor         # user or system that caused it
  occurredAt    # timestamp
  sequence      # monotonic ordering within an aggregate
}
```

Events are never modified or deleted.

---

## Categories & Events

### Planning
```
InitiativeCreated
EpicCreated
StoryCreated
TaskCreated
TaskUpdated
TaskReady
TaskCancelled
```

### Runtime
```
StoryExecutionCreated
StoryStarted
TaskStarted
CapabilityExecutionStarted
ProviderExecutionScheduled
ProviderExecutionStarted
ProviderExecutionSucceeded
ProviderExecutionFailed
RetryScheduled
CapabilityExecutionCompleted
CapabilityExecutionFailed
TaskCompleted
TaskFailed
TaskExecutionCancelled
StoryExecutionCompleted
StoryExecutionFailed
```

### Decision
```
HumanRequestCreated
HumanRequestViewed
DecisionRequested
DecisionSubmitted
DecisionApplied
HumanRequestResolved
```

### Artifact
```
ArtifactCreated
ArtifactVersionCreated
ArtifactReviewed
ArtifactApproved
```

### Notification
```
NotificationCreated
NotificationDismissed
```

### System
```
WorkflowSignalSent
WorkflowQueryExecuted
AdapterErrorRaised
```

---

## Consumers (Read Models)

Each consumer builds and owns its own projection:

| Consumer | Built from | Purpose |
| -------- | ---------- | ------- |
| **Timeline** | all Runtime + Decision + Artifact events | per-execution audit history |
| **Attention Queue** | HumanRequest*, *Failed events | cross-initiative work needing humans |
| **Metrics** | Runtime events | progress, durations, success rates |
| **Analytics** | all events | trends, cost (future) |
| **Notifications** | Notification*, selected Runtime events | transient user awareness |
| **Search** | Planning + Artifact events | discovery (future) |

---

## Ordering & Replay

- Events are ordered per aggregate by `sequence`.
- Read models are deterministically rebuildable by replaying events — enabling
  auditability, debugging, and future execution replay.
- Workflow-engine events (from Temporal) are persisted as Runtime events by the
  Workflow Engine Context before projection.

---

## Relationship to the Timeline

The **Timeline** is the primary, user-facing projection of Runtime/Decision/
Artifact events for a given Story or Task Execution. It is append-only and never
edited. Examples of surfaced entries:

```
Execution Started
Capability Started
Provider Failed
Retry Scheduled
Approval Requested
Decision Received
Artifact Produced
Execution Completed
```

See [../observability/observability.md](../observability/observability.md) for
retention and querying.
