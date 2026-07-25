# /specs/execution-model.md

# Execution Model

## Overview

Planning objects describe **intent**.

Execution objects describe **runtime**.

The same Task may execute multiple times without modifying planning.

```
Task
   │
   ├── Execution #1 (Failed)
   │
   ├── Execution #2 (Cancelled)
   │
   └── Execution #3 (Completed)
```

Planning is immutable.

Execution is ephemeral.

---

# Execution Hierarchy

```
StoryExecution
    │
    ├── TaskExecution
    │      │
    │      ├── AgentExecution
    │      ├── AgentExecution
    │      └── AgentExecution
    │
    └── TaskExecution
```

Each execution owns its own lifecycle.

---

# Story Execution

Responsibilities

- Aggregate Task status
- Aggregate Artifacts
- Calculate Story progress
- Surface Human Requests

Story Execution never performs work.

It orchestrates.

---

# Task Execution

Responsibilities

- Execute business work
- Coordinate Agents
- Produce outputs
- Wait for Decisions

---

# Agent Execution

Responsibilities

- Prompt LLMs
- Call MCP tools
- Search
- Write files
- Execute code
- Produce intermediate outputs

---

# Retry Policy

Retries always create a new Execution.

Planning objects are never modified.

```
Task

↓

Execution 1

↓

Failed

↓

Retry

↓

Execution 2
```

Previous executions remain available for audit.

---

# Cancellation

Cancelling an execution never deletes history.

Status becomes

Cancelled

Timeline remains intact.

---

# Completion

Completion requires

- Workflow completed
- Required Artifacts produced
- Required Decisions completed

Only then may the Story advance.
