# Functional Requirements

## Planning

The system shall support:

- Workspace management
- Epic CRUD
- Story CRUD
- Task CRUD
- Task dependencies
- Acceptance Criteria

---

## Execution

The system shall support:

- Start Story
- Start Task
- Cancel Task
- Retry Task

---

## Runtime

The system shall display:

- Current status
- Timeline
- Logs
- Running agent
- Waiting reason
- Produced artifacts

---

## Human Interaction

The system shall support:

- Approve
- Reject
- Clarify
- Continue
- Abort

---

## Monitoring

The system shall aggregate:

- Waiting approvals
- Waiting clarification
- Failures
- Completed executions

---

## Persistence

Planning state shall survive application restart.

Execution history shall survive workflow completion.

---

## API

Backend exposes command-oriented APIs.

Workflow engines remain hidden behind adapters.
