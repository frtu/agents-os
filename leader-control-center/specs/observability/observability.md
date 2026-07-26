# Observability & Non-Functional Requirements

Observability is intrinsic: every execution produces a complete, immutable
Timeline. This spec also collects the system-wide non-functional requirements
(NFRs) that constrain the whole spec-kit.

---

## Timeline & Audit

- Every execution emits an append-only Timeline from domain events (see
  [../domain/event-model.md](../domain/event-model.md)).
- History is never modified.
- Every Decision is traceable to user, timestamp, execution, and reason.
- Read models (Timeline, Attention, Metrics) are rebuildable by replaying events.

---

## Metrics

Projected from Runtime events:

- execution counts by status
- durations (task, capability, provider)
- success / failure / retry rates
- attention latency (time a Human Request waits)

---

## Logging & Tracing

- Structured logs keyed by `initiativeId`, `executionId`, `eventId`.
- Provider Executions capture provider-side logs as artifacts/log references, not
  in the event log.
- No secrets in logs or events (see [../auth/auth.md](../auth/auth.md)).

---

## Non-Functional Requirements

### Scalability
Support hundreds of concurrent executions.

### Reliability
Workflow state must survive process restart (delegated to the durable engine).
Planning state survives application restart. Execution history survives workflow
completion.

### Observability
Every execution produces a complete timeline.

### Extensibility
Workflow engines are replaceable (adapter port). Scheduling strategies and
execution strategies are replaceable (strategy interfaces).

### Testability
Every business rule must be testable **without** requiring Temporal — the engine
is mockable behind the WorkflowEngine port (see
[../workflow-engine/workflow-engine.md](../workflow-engine/workflow-engine.md)).

### Performance
Dashboard loads within 2 seconds for 100 active executions.

### Availability
The frontend remains usable while individual workflow executions fail.

### Security
Only authorized users may start executions, approve decisions, or cancel
workflows (see [../permissions/permissions.md](../permissions/permissions.md)).

### Auditability
Every decision is traceable to user, timestamp, execution, and reason.

---

## Health & Readiness

- Backend exposes liveness/readiness endpoints.
- Workflow engine connectivity is a readiness dependency but its failure must not
  crash the API (Availability). See [../deployment/deployment.md](../deployment/deployment.md).
