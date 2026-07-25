# Non Functional Requirements

## Scalability

Support hundreds of concurrent executions.

---

## Reliability

Workflow state must survive process restart.

---

## Observability

Every execution produces a complete timeline.

---

## Extensibility

Workflow engines must be replaceable.

Scheduling strategies must be replaceable.

---

## Testability

Every business rule should be testable without requiring Temporal.

---

## Performance

Dashboard loads within 2 seconds for 100 active executions.

---

## Availability

Frontend remains usable while individual workflow executions fail.

---

## Security

Only authorized users may:

- start executions
- approve decisions
- cancel workflows

---

## Auditability

Every decision must be traceable to:

- user
- timestamp
- execution
- reason
