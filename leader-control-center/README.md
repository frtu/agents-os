# Leader Control Center

> As leaders, we don't have time to only solve one task as a time.

A human-in-the-loop control center for supervising durable AI workflows.

---

# Vision

Modern AI agents are capable of executing work that spans minutes, hours, or even days. Unlike chat interactions, these workflows frequently pause to request clarification, approval, or additional information.

As a leader, you don't have time to constantly context-switch between conversations and monitor every running workflow.

**Leader Control Center** is a supervisory application that provides a single operational view over all long-running AI executions, allowing leaders to:

- Plan work
- Launch executions
- Monitor progress
- Respond to requests for attention
- Review outputs
- Continue execution

without losing context.

The application is **not an orchestration engine**.

It is a **Meta Orchestration Control Plane** built on top of durable workflow engines.

---

# Goals

The application aims to:

- Supervise multiple concurrent AI workflows
- Organize work into business outcomes instead of chats
- Reduce interruption fatigue
- Keep humans in control of strategic decisions
- Support durable, resumable execution
- Provide complete execution history and traceability
- Scale from manual execution to autonomous orchestration

---

# Core Principles

## Human-in-the-loop

Humans remain responsible for:

- Prioritization
- Approvals
- Clarifications
- Strategic decisions

AI agents remain responsible for execution.

---

## Planning ≠ Runtime

Planning and execution are intentionally separated.

Planning describes **what should be built**.

Runtime describes **what is currently happening**.

This distinction allows executions to be retried, cancelled or restarted without changing the original plan.

---

## Progressive Automation

The system starts with manual orchestration.

Future versions progressively automate decision making without requiring architectural changes.

```
Leader
        ↓
Manual Scheduling (MVP)

↓

Dependency Scheduling

↓

AI Planning
```

---

# Domain Model

```
Workspace
│
├── Epic
│
├── Story
│     │
│     ├── Task
│     ├── Dependency
│     └── Acceptance Criteria
│
└── Runtime
      │
      ├── Story Execution
      │      │
      │      ├── Task Execution
      │      │      │
      │      │      ├── Agent Execution
      │      │      └── Agent Execution
      │      │
      │      ├── Timeline
      │      ├── Human Requests
      │      ├── Decisions
      │      └── Artifacts
      │
      └── Notifications
```

---

# Core Concepts

## Workspace

Top-level container.

Future versions may support multiple workspaces.

---

## Epic

Represents a business initiative.

Examples:

- Promotion
- Platform Modernization
- Search V2
- AI Adoption

Epics should remain achievable within approximately one month.

---

## Story

Represents a business deliverable.

Examples:

- Write promotion document
- Create architecture proposal
- Build migration plan

Stories move across the Kanban board.

---

## Task

A unit of executable work.

Examples:

- Research
- Write document
- Generate diagram
- Review architecture

Tasks define **what** should happen.

They are not execution instances.

---

## Story Execution

Runtime instance of a Story.

Responsible for orchestrating Task executions.

---

## Task Execution

Runtime instance of a Task.

Responsible for coordinating one or more Agent executions.

---

## Agent Execution

Lowest execution level.

Responsible for:

- LLM interaction
- Tool usage
- MCP integration
- Search
- Code generation
- Document generation

---

# Runtime Objects

## Human Request

Represents something requiring human attention.

Examples:

- Approval required
- Clarification required
- Tool permission
- Missing information
- Budget exceeded

---

## Decision

Represents a human response.

Examples:

- Approve
- Reject
- Clarify
- Continue
- Abort
- Select option

Workflows wait for Decisions instead of approvals.

---

## Artifact

Output produced by an execution.

Examples:

- Markdown
- Specification
- Presentation
- Diagram
- Spreadsheet
- Source code
- Image

Artifacts are first-class domain objects.

---

## Timeline

Every execution produces an immutable event timeline.

Examples:

- Started
- Waiting Approval
- Clarification Requested
- Continued
- Failed
- Completed

---

# Planning Workflow

```
Epic

↓

Story

↓

Task

↓

Ready
```

Planning remains stable throughout execution.

---

# Execution Workflow

```
Story Execution

↓

Task Execution

↓

Agent Execution
```

Each level owns a different responsibility.

---

# Task States

Planning states.

```
Draft

↓

Ready

↓

Running

↓

Waiting

↓

Blocked

↓

Completed

↓

Cancelled
```

Only **Ready** tasks may be started.

---

# Scheduling Strategy

The application intentionally separates scheduling policy from execution.

```
Story Workflow

↓

Scheduling Strategy

├── Manual Scheduling
├── Dependency Scheduling
└── AI Planning
```

## MVP

Manual Scheduling.

The leader explicitly starts every task.

```
Leader

↓

Start Task

↓

Backend

↓

Workflow Engine
```

## Future

Dependency Scheduling.

Tasks automatically start when dependencies are satisfied.

## Future

AI Planning.

AI dynamically creates, reprioritizes and launches Tasks.

---

# Workflow Hierarchy

```
Story Execution

├── Task Execution

│     ├── Agent Execution
│     ├── Agent Execution
│     └── Agent Execution

└── Task Execution
```

This hierarchy enables:

- Parallel execution
- Retry
- Pause
- Resume
- Human approval
- Dynamic fan-out

---

# User Interface

The primary interface is a Kanban board.

Each Epic appears as a collapsible vertical drawer.

Inside each Epic:

```
Todo

Ready

Running

Blocked

Completed
```

Selecting a Story opens its execution details.

Execution details include:

- Timeline
- Running Tasks
- Human Requests
- Artifacts
- Logs
- Chat
- Decisions

---

# Attention Queue

The application continuously aggregates requests requiring human attention.

Examples:

- Waiting approval
- Clarification required
- Execution failed
- Tool permission
- Budget approval

This allows leaders to supervise many concurrent workflows without constant interruption.

---

# Architecture

```
                React Frontend
                       │
             REST + WebSocket
                       │
                Backend API
                       │
          Workflow Management Layer
                       │
          Workflow Engine Adapter
                       │
        ┌──────────────┴──────────────┐
        │                             │
    Temporal                  Future Engines
```

The backend owns the business model.

Workflow engines own execution.

The frontend never communicates directly with workflow engines.

---

# Technology Stack

## Frontend

- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- Zustand

---

## Backend

- Python
- FastAPI
- OpenAPI
- PostgreSQL

---

## Workflow

Initial target:

- Temporal

Future:

- Additional workflow engines via adapters

---

# API Philosophy

The API exposes business commands instead of CRUD operations.

Examples:

```
POST /stories

POST /tasks

POST /tasks/{id}/start

POST /executions/{id}/approve

POST /executions/{id}/clarify

POST /executions/{id}/cancel

POST /executions/{id}/retry
```

The backend translates these commands into workflow engine operations.

---

# MVP Scope

The first version intentionally focuses on simplicity.

Features:

- Epic management
- Story management
- Task management
- Manual task execution
- Temporal integration
- Execution monitoring
- Timeline
- Human decisions
- Artifact viewing
- Attention queue

Automation is intentionally deferred.

---

# Future Evolution

Without changing the architecture, future versions can introduce:

- Dependency-based scheduling
- AI planning
- Dynamic task creation
- Multiple workflow engines
- Multiple workspaces
- Team collaboration
- Notifications
- Plugin ecosystem
- MCP integrations
- Analytics
- Cost tracking
- Execution replay

---

# Guiding Principle

> Build the simplest system that supports today's workflow while making tomorrow's automation a configuration change rather than an architectural rewrite.