# /specs/event-model.md

# Event Model

Everything that happens produces an immutable event.

Events are append-only.

---

# Event Categories

Planning

Runtime

Decision

Artifact

Notification

System

---

# Planning Events

EpicCreated

StoryCreated

TaskCreated

TaskUpdated

TaskDeleted

---

# Runtime Events

StoryStarted

TaskStarted

TaskCompleted

TaskFailed

ExecutionCancelled

ExecutionRetried

---

# Decision Events

DecisionRequested

DecisionViewed

DecisionSubmitted

DecisionApplied

---

# Artifact Events

ArtifactCreated

ArtifactVersionCreated

ArtifactReviewed

ArtifactApproved

---

# Notification Events

NotificationCreated

NotificationDismissed

---

# Event Consumers

Timeline

Notifications

Metrics

Analytics

Audit Log

Search

Future Automations

Each consumer builds its own read model.

No consumer owns the source of truth.
