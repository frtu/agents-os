# Leader Control Center

> As leaders, we don't have time to only solve one task at a time.

A human-in-the-loop control center for supervising durable AI workflows.

---

# Vision

Modern AI agents are capable of executing work that spans minutes, hours, or even days. Unlike conversational assistants, these workflows frequently pause to request clarification, approvals, permissions, or additional information before they can continue.

As leaders, we don't have time to constantly context-switch between dozens of conversations just to answer simple questions like:

- "Can I continue?"
- "Which option should I choose?"
- "Can I access this system?"
- "Please review this document."

Today's AI interfaces are conversation-centric.

Leader Control Center is execution-centric.

Instead of managing one AI conversation at a time, leaders supervise multiple concurrent initiatives through a single operational control center.

The application allows leaders to:

- Plan work
- Launch AI executions
- Monitor progress
- Respond to human requests
- Review generated artifacts
- Continue execution
- Audit execution history

without losing context.

The application is **not** a workflow engine.

It is a **Meta Orchestration Control Plane** built on top of durable workflow engines.

---

# Goals

Leader Control Center aims to become the operational console for durable AI execution.

The application should allow leaders to:

- supervise multiple concurrent AI initiatives
- organize work around business outcomes
- reduce interruption fatigue
- maintain human strategic control
- support long-running execution
- provide complete execution history
- progressively automate execution over time
- remain independent of any specific workflow engine or AI provider

---

# Non Goals

Leader Control Center is NOT:

- a workflow engine
- a chat application
- a project management replacement
- an LLM framework
- an MCP server
- an AI coding IDE

Instead, it coordinates these systems.

---

# Product Principles

## Human First

Humans remain responsible for:

- planning
- priorities
- approvals
- clarifications
- strategic decisions

AI remains responsible for execution.

---

## Business First

The platform models business outcomes.

Workflow engines, LLMs, MCP servers and providers are implementation details hidden behind the execution layer.

---

## Human View ≠ System View

Leaders naturally think in terms of business initiatives.

Examples:

- Platform Modernization
- Create Agent Orchestration Flow
- Agent Worklfow V2
- AI Adoption
- Database Migration

Internally, however, planning is still represented using familiar concepts:

- Epic
- Story
- Task

This separation allows the system to present a business-centric experience while preserving a clean and extensible planning model.

---

## Planning ≠ Runtime

Planning defines what should happen.

Runtime records what is happening.

Planning should remain stable throughout execution.

Executions may:

- retry
- fail
- pause
- resume
- restart

without modifying planning.

---

## Progressive Automation

Every autonomous capability must first exist as an explicit capability.

Users should always be able to choose between:

- explicit planning
- AI-assisted planning
- fully autonomous planning

without changing the architecture.

The evolution path should look like:

Leader

↓

Manual Scheduling (MVP)

↓

Dependency Scheduling

↓

AI Planning

↓

Autonomous Coordination

---

# Domain Overview

Leader Control Center separates the platform into two complementary perspectives.

## Human View

The user supervises **Initiatives**.

An Initiative represents a business outcome.

Examples:

- Platform Modernization
- Create Agent Orchestration Flow
- Agent Worklfow V2
- AI Adoption
- Database Migration

Everything the leader needs is grouped under an Initiative:

- planning
- progress
- executions
- waiting approvals
- artifacts
- history

The leader never needs to understand workflow engine concepts.

---

## System View

Internally, an Initiative is composed of:

Workspace

↓

Epic

↓

Story

↓

Task

↓

Execution

↓

Capability Execution

↓

Provider Execution

The planning hierarchy remains stable while runtime evolves independently.

---

# Domain Model

From a leader's perspective, every business outcome is represented as an **Initiative**.

```
Portfolio
│
└── Initiative (Human View)
      │
      ├── Planning
      │     │
      │     ├── Epic
      │     │      │
      │     │      ├── Story
      │     │      │      │
      │     │      │      ├── Task
      │     │      │      ├── Dependency
      │     │      │      └── Acceptance Criteria
      │     │
      │     └── Planning Metadata
      │
      └── Runtime
            │
            ├── Story Execution
            │      │
            │      ├── Task Execution
            │      │      │
            │      │      ├── Capability Execution
            │      │      │      │
            │      │      │      ├── Provider Execution
            │      │      │      ├── Provider Execution
            │      │      │      └── Provider Execution
            │      │      │
            │      │      ├── Timeline
            │      │      ├── Human Requests
            │      │      ├── Decisions
            │      │      └── Artifacts
            │      │
            │      └── Metrics
            │
            └── Attention Queue
```

Planning remains immutable.

Runtime is disposable.

History is permanent.

---

# Core Concepts

## Portfolio

The top-level organizational boundary backed by a `Workspace`.

A Portfolio owns:

- Initiatives
- Users
- Providers
- Credentials
- Capability Catalog
- Integrations
- Default AI configuration

Future versions may support multiple Portfolio.

---

## Initiative

The primary business object presented to leaders.

An Initiative represents a business outcome.

Examples:

- Platform Modernization
- Create Agent Orchestration Flow
- Agent Worklfow V2
- AI Adoption
- Database Migration

An Initiative groups:

- planning
- runtime
- decisions
- artifacts
- history

Internally an Initiative is backed by one or more Epics together with their runtime executions.

---

## Epic

Represents the primary planning container.

An Epic groups Stories contributing toward one Initiative.

Epics remain implementation details.

Leaders interact with Initiatives rather than Epics.

Epics should remain achievable within approximately one month.

---

## Story

Represents a business deliverable.

Examples:

- Write promotion document
- Create architecture proposal
- Build migration strategy

Stories progress through the planning board and own one or more Tasks.

---

## Task

A Task represents a unit of planned work.

A Task defines **what** should be accomplished.

A Task never defines **how** execution occurs.

Execution decisions are deferred until runtime.

Tasks may be planned in two different modes:

- Structured
- Goal-Oriented

## Planning Modes

Leader Control Center intentionally separates **planning** from **execution**.

Planning defines business intent.

Execution determines how that intent is fulfilled.

Every Task is created using exactly one **Planning Mode**.

```
Planning Mode

├── Structured
└── Goal-Oriented
```

Both planning modes ultimately normalize into the same execution model.

This allows users to progressively adopt AI planning without changing the runtime architecture.

---

### Structured Planning

Structured Planning is the default.

The leader explicitly defines:

- Task name
- Capability
- Dependencies
- Acceptance Criteria

Example

```
Task

Write Promotion Document

Capability

Write Markdown

Acceptance Criteria

- Executive quality
- Less than three pages
- Ready for manager review
```

This mode provides predictable and deterministic execution.

It is recommended for production workflows.

---

### Goal-Oriented Planning

Goal-Oriented Planning delegates task decomposition to the AI Planner.

Instead of selecting a Capability, the leader describes the desired outcome.

Example

```
Goal

Prepare a promotion package that demonstrates my
technical leadership and business impact.

Success Criteria

- Executive quality
- Metrics included
- Ready for review
```

The AI Planner determines:

- Capabilities
- Dependencies
- Execution order
- Suggested providers

before execution begins.

---

### Progressive Planning

The application intentionally supports increasing levels of autonomy.

```
Structured

↓

AI Suggestions

↓

Goal-Oriented

↓

Autonomous Planning
```

Users can gradually adopt AI planning without changing their workflows.

---

# Runtime Objects

Planning creates runtime objects.

Planning itself is never modified.

```
Planning

↓

Execution

↓

History
```

Every execution is immutable history.

---

## Story Execution

Represents one runtime instance of a Story.

Responsibilities:

- orchestrate Tasks
- monitor progress
- aggregate status
- produce artifacts
- expose timeline

---

## Task Execution

Represents one execution instance of a Task.

Responsibilities:

- invoke capabilities
- monitor execution
- request human interaction
- publish runtime events

A Task may execute multiple times without modifying planning.

---

## Capability Execution

Capability Execution represents **what ability is required**.

Examples:

- Research
- Write
- Review
- Search
- Diagram
- Code
- Translate
- Test
- Analyze
- Summarize

Capabilities are stable business concepts.

They are intentionally independent from AI providers.

---

## Provider Execution

Provider Execution represents the concrete implementation.

Examples

```
OpenAI

Anthropic

Gemini

Cursor

GitHub MCP

Slack MCP

Temporal Activity

Human
```

Providers may change over time.

Capabilities remain stable.

---

# Capability Model

Capabilities describe **what the platform can do**.

They do not describe:

- prompts
- LLMs
- providers
- execution engines

```
Capability

id

name

description

inputs

outputs

supported providers
```

Example

```
Capability

Write Markdown

Inputs

Markdown Specification

Outputs

Markdown Document
```

---

## Capability Catalog

Capabilities are reusable across every Initiative.

```
Capability Catalog

Research

Search

Review

Write Markdown

Generate Diagram

Generate Presentation

Generate Code

Analyze

Summarize

Translate

Test

Deploy

Review Architecture
```

The Capability Catalog is managed at Workspace level.

---

# Provider Model

Providers execute Capabilities.

Providers are completely interchangeable.

Examples

```
OpenAI

Anthropic

Google Gemini

GitHub Copilot

Cursor

Claude Code

Human

Slack MCP

GitHub MCP

Temporal Activity
```

Providers expose a common contract.

```
supports()

estimate()

execute()

cancel()

resume()
```

Providers should never contain business logic.

---

# Execution Strategy

Execution Strategy determines **how** a Capability is executed.

```
Capability

↓

Execution Strategy

↓

Provider

↓

Execution
```

Separating strategy from provider enables progressively more advanced orchestration.

---

## Supported Strategies

### Single Provider

```
Capability

↓

Claude
```

---

### Retry

```
Claude

↓

Retry

↓

Retry

↓

Completed
```

---

### Parallel

```
Capability

↓

Claude

GPT

Gemini
```

---

### Consensus

```
Capability

↓

Claude

GPT

Gemini

↓

Merge

↓

Result
```

---

### Human Review

```
Capability

↓

LLM

↓

Human Approval

↓

Continue
```

---

### Pipeline

```
Research

↓

Write

↓

Review

↓

Publish
```

---

### Loop

```
Generate

↓

Evaluate

↓

Improve

↓

Satisfied?
```

---

### Fan-Out

```
Research

↓

Region A

Region B

Region C

↓

Merge
```

Execution Strategies are implementation details and may evolve independently from planning.

---

# Human Requests

The platform pauses execution only through Human Requests.

Examples

- Approval
- Clarification
- Budget
- Tool Permission
- Missing Information
- Choose Option
- Risk Acceptance

Human Requests are first-class runtime objects.

---

# Decisions

Every Human Request produces exactly one Decision.

Supported decisions:

- Approve
- Reject
- Clarify
- Continue
- Abort
- Retry
- Select Option

Decision history is immutable.

---

# Artifact Model

Artifacts are first-class business objects.

Examples

- Markdown
- Specification
- Diagram
- Image
- PDF
- Spreadsheet
- Presentation
- Source Code
- Test Report

Artifacts are immutable.

Updating an Artifact always creates a new version.

```
Artifact

id

type

version

owner

created by

created at

metadata
```

---

# Timeline

Everything that happens becomes an immutable event.

Examples

```
Execution Started

Capability Started

Capability Completed

Provider Failed

Retry Scheduled

Approval Requested

Decision Received

Artifact Produced

Execution Completed
```

The Timeline is append-only.

History is never modified.

---

# Workflow Hierarchy

```
Story Execution

│

├── Task Execution

│      │

│      ├── Capability Execution

│      │       │

│      │       ├── Provider Execution

│      │       ├── Provider Execution

│      │       └── Provider Execution

│      │

│      ├── Human Requests

│      ├── Artifacts

│      └── Timeline

│

└── Task Execution
```

Every layer has exactly one responsibility.

Planning never depends on Runtime.

Runtime never modifies Planning.

---

# State Machines

## Planning

```
Draft

↓

Ready

↓

Archived
```

---

## Task

```
Draft

↓

Ready

↓

Cancelled
```

---

## Story Execution

```
Created

↓

Running

↓

Waiting

↓

Completed

↓

Cancelled

↓

Failed
```

---

## Capability Execution

```
Pending

↓

Running

↓

Waiting

↓

Completed

↓

Failed
```

---

## Provider Execution

```
Scheduled

↓

Running

↓

Succeeded

↓

Failed

↓

Cancelled
```

Provider failures do not necessarily imply Capability failures.

Execution Strategy determines whether retries, failover, consensus, or human intervention should occur.


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

* LLM interaction
* MCP integration
* Tool usage
* Search and retrieval
* Code generation
* Document generation

---

# Runtime Objects

## Human Request

Represents something requiring human attention.

Examples:

* Approval required
* Clarification required
* Tool permission
* Missing information
* Budget exceeded

---

## Decision

Represents a human response.

Examples:

* Approve
* Reject
* Clarify
* Continue
* Abort
* Select option

Workflows wait for Decisions instead of approvals.

---

## Artifact

Output produced by an execution.

Examples:

* Markdown
* Specification
* Presentation
* Diagram
* Spreadsheet
* Source code
* Image

Artifacts are first-class domain objects.

---

## Timeline

Every execution produces an immutable event timeline.

Examples:

* Started
* Waiting Approval
* Clarification Requested
* Continued
* Failed
* Completed

---

# Planning Workflow

Planning is the internal representation of an Initiative.

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

* Parallel execution
* Retry
* Pause
* Resume
* Human approval
* Dynamic fan-out

---

# User Interface

The primary interface is a Kanban board.

Each **Initiative** (backed by an Epic) appears as a collapsible vertical drawer.

Inside each Initiative:

```
Todo

Ready

Running

Blocked

Completed
```

Selecting a Story opens its execution details.

Execution details include:

* Timeline
* Running Tasks
* Human Requests
* Artifacts
* Logs
* Chat
* Decisions

---

# Attention Queue

The application continuously aggregates requests requiring human attention.

Examples:

* Waiting approval
* Clarification required
* Execution failed
* Tool permission
* Budget approval

This allows leaders to supervise many concurrent workflows without constant interruption.

---

# Human View vs Internal Model

The application intentionally separates presentation from implementation.

## Human View

```
Workspace

↓

Initiative

↓

Current Progress

↓

Decisions

↓

Artifacts
```

## Internal Planning Model

```
Workspace

↓

Epic

↓

Story

↓

Task

↓

Execution
```

This mapping allows future automation without changing the user experience while preserving compatibility with established planning concepts.

| Human View   | Internal Domain            |
| ------------ | -------------------------- |
| Initiative   | Epic + Runtime             |
| Progress     | Story Executions           |
| Running Work | Task Executions            |
| AI Activity  | Agent Executions           |
| Decisions    | Human Requests + Decisions |
| Outputs      | Artifacts                  |
| History      | Timeline                   |

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

* React
* TypeScript
* Tailwind CSS
* shadcn/ui
* TanStack Query
* Zustand

---

## Backend

* Python
* FastAPI
* OpenAPI
* PostgreSQL

---

## Workflow

Initial target:

* Temporal

Future:

* Additional workflow engines via adapters

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

* Epic management
* Story management
* Task management
* Manual task execution
* Temporal integration
* Execution monitoring
* Timeline
* Human decisions
* Artifact viewing
* Attention queue

Automation is intentionally deferred.

---

# Future Evolution

Without changing the architecture, future versions can introduce:

* Dependency-based scheduling
* AI planning
* Dynamic task creation
* Multiple workflow engines
* Multiple workspaces
* Team collaboration
* Notifications
* Plugin ecosystem
* MCP integrations
* Analytics
* Cost tracking
* Execution replay

---

# Guiding Principle

> Build the simplest system that supports today's workflow while making tomorrow's automation a configuration change rather than an architectural rewrite.
