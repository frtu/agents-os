# Domain Model

## Planning Context

Workspace

Represents an isolated planning environment.

Contains:

- Epics
- Stories
- Tasks

---

Epic

Represents a business objective.

Examples:

- Promotion
- AI Adoption

Lifecycle:

Draft → Active → Completed

---

Story

Represents one deliverable.

Examples:

- Promotion Resume
- Architecture Proposal
- Migration Plan

Owns:

- Tasks
- Dependencies
- Acceptance Criteria

Lifecycle:

Todo → Ready → Executing → Review → Done

---

Task

Represents executable work.

Examples:

- Research
- Generate Diagram
- Review Proposal

Tasks never represent runtime.

---

Dependency

Represents prerequisite relationships between Tasks.

Initially informational.

Future versions enable automatic scheduling.

---

Acceptance Criteria

Defines completion conditions for a Story.

---

## Runtime Context

StoryExecution

Runtime instance of a Story.

Coordinates TaskExecutions.

---

TaskExecution

Runtime instance of a Task.

Coordinates AgentExecutions.

---

AgentExecution

Lowest execution unit.

Responsible for:

- Prompt execution
- Tool usage
- MCP
- Search
- Generation

---

Timeline

Immutable execution history.

---

HumanRequest

Represents work requiring human attention.

Examples:

- Approval
- Clarification
- Budget
- Permission

---

Decision

Human response to a HumanRequest.

---

Artifact

Output produced by execution.

Examples:

Markdown

Presentation

Spreadsheet

Image

Code

Diagram

---

Notification

Represents surfaced events requiring user awareness.
