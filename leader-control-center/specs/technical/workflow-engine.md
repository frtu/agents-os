# /specs/workflow-engine.md

# Workflow Engine

## Responsibility

Workflow engines execute work.

They do NOT own:

- Epics
- Stories
- Planning
- Priorities

They only execute Tasks.

---

# Workflow Hierarchy

```
Story Workflow

↓

Task Workflow

↓

Agent Workflow
```

---

## Story Workflow

Responsibilities

- monitor Story completion
- coordinate Task Workflows
- aggregate Artifacts
- expose Story status

Future versions may automatically schedule Tasks.

MVP only observes manual execution.

---

## Task Workflow

Responsibilities

- execute business work
- coordinate Agent Workflows
- wait for Decisions
- retry failures
- produce Artifacts

---

## Agent Workflow

Responsibilities

- call LLMs
- use MCP tools
- search
- generate documents
- execute code

---

# Workflow Signals

External commands become workflow signals.

Examples

```
Approve

Reject

Clarify

Continue

Cancel
```

---

# Workflow Queries

The backend may query workflows for:

Current Step

Current Agent

Waiting Reason

Progress

Estimated Completion

---

# Workflow Events

The workflow engine emits domain events.

Examples

```
ExecutionStarted

ArtifactProduced

DecisionRequested

DecisionReceived

ExecutionCompleted

ExecutionFailed
```

The backend persists these as Timeline entries.

---

# Scheduling

Scheduling is intentionally delegated.

Current implementation

```
ManualSchedulingStrategy
```

Future

```
DependencySchedulingStrategy

AIPlanningStrategy
```

The workflow hierarchy remains unchanged.
