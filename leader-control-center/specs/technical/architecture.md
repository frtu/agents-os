# /specs/architecture.md

# Architecture

## Overview

Leader Control Center follows a layered architecture separating:

- User Interface
- Business Domain
- Runtime Orchestration
- Workflow Engine
- Infrastructure

```
                React UI
                    │
            REST + WebSocket
                    │
────────────────────────────────────────
            Backend API Layer
────────────────────────────────────────
 Application Services / Commands
────────────────────────────────────────
 Domain Model (Planning + Runtime)
────────────────────────────────────────
 Workflow Engine Adapter
────────────────────────────────────────
        Temporal / Future Engines
────────────────────────────────────────
```

The UI never communicates directly with workflow engines.

The Workflow Engine never owns planning.

The Backend is the single source of truth.

---

# Architectural Principles

## Planning and Runtime are separate bounded contexts

Planning changes slowly.

Runtime changes constantly.

The two contexts communicate through commands and events.

---

## Business Model is Workflow Agnostic

The backend never exposes Temporal concepts.

Instead of exposing:

- WorkflowId
- RunId
- Activity

It exposes:

- StoryExecution
- TaskExecution
- Timeline
- Decision
- HumanRequest

---

## Everything is Command Driven

Clients never mutate state directly.

Instead they send Commands.

Examples

```
CreateStory

StartTask

ApproveDecision

RetryExecution

CancelExecution
```

Commands create Events.

Events update Read Models.

---

## Event Driven Runtime

Runtime state is projected from immutable events.

Examples

```
StoryStarted

TaskStarted

DecisionRequested

DecisionProvided

ExecutionFailed

ExecutionCompleted
```

This provides:

- auditability
- replay
- debugging
- analytics

---

## Ports and Adapters

Business logic depends only on interfaces.

```
Application

↓

WorkflowEngine

↓

Temporal Adapter
```

Later

```
Application

↓

WorkflowEngine

↓

Temporal

↓

LangGraph

↓

Future Engine
```

No business logic changes.
