# 01-domain.md

> **Purpose**
>
> This document defines the business domain model for Leader Control Center.
>
> Everything else (API, database, frontend, Temporal workflows, provider integrations, MCP, etc.) derives from this model.
>
> This specification intentionally describes **business concepts**, not implementation details.

---

# Domain Philosophy

Leader Control Center models **business outcomes**, not AI conversations.

The platform exists to help leaders supervise long-running initiatives involving humans, AI, workflow engines and external systems.

Unlike traditional AI applications, conversations are **not** first-class objects.

Instead, the platform models:

```
Business Outcome
↓
Planning
↓
Execution
↓
Artifacts
↓
Business Decision
```

The implementation technology (LLMs, Temporal, MCP, APIs, providers) is intentionally hidden behind stable business abstractions.

---

# Domain Principles

## 1. Business First

The domain language should be understandable by leaders.

Good domain concepts:
- Initiative
- Story
- Task
- Capability
- Artifact
- Decision

Poor domain concepts:
- Prompt
- Agent
- GPT
- Claude
- Workflow Activity

Technology changes.

Business concepts remain stable.

---

## 2. Human-Centric

Humans own:
- objectives
- priorities
- planning
- approvals
- strategic decisions

AI owns execution.

The platform never removes human ownership.

Instead, it progressively increases automation.

---

## 3. Planning is Intent

Planning represents intent.

Planning answers:

> What should happen?

Planning should remain stable.

Planning is **not** execution.

---

## 4. Runtime is Observation

Runtime records what actually happened.

Runtime answers:

> What is happening?

Runtime is disposable.

History is permanent.

---

## 5. Progressive Autonomy

Every autonomous feature must first exist as an explicit feature.

Example:

```
Manual Task
↓
AI Assisted Task
↓
Goal-Oriented Task
↓
Autonomous Planning
```

The architecture should never require redesign as automation increases.

---

# Ubiquitous Language

The following terminology must be used consistently throughout the platform.

| Term | Meaning |
|-------|---------|
| Workspace | Organizational boundary |
| Initiative | Business outcome supervised by a leader |
| Epic | Planning container backing an Initiative |
| Story | Business deliverable |
| Task | Planned unit of work |
| Execution | Runtime instance |
| Capability | Business skill required for execution |
| Provider | Concrete implementation of a Capability |
| Strategy | How Providers are orchestrated |
| Artifact | Produced output |
| Human Request | Runtime pause awaiting human input |
| Decision | Human response |
| Timeline | Immutable execution history |

---

# Aggregate Roots

The platform intentionally exposes very few aggregate roots.

```
Workspace
Initiative
Execution
Capability Catalog
```

Everything else belongs to one of these aggregates.

This minimizes coupling and simplifies future evolution.

---

# Aggregate: Workspace

The Workspace is the top-level organizational boundary.

Responsibilities:
- users
- permissions
- provider registry
- capability catalog
- integrations
- AI defaults
- workspace settings

Owns:

```
Workspace
├── Initiatives
├── Capability Catalog
├── Provider Registry
└── Integrations
```

The Workspace never owns runtime state directly.

---

# Aggregate: Initiative

The Initiative is the primary business object.

This is the object leaders think about.

Examples:
- Promotion to P3
- Search Platform V2
- Platform Modernization
- AI Adoption
- Notification Platform

Everything presented in the UI belongs to an Initiative.

---

## Initiative Responsibilities

An Initiative owns planning.

Specifically:
- objective
- priority
- epics
- stories
- tasks
- acceptance criteria
- planning metadata

An Initiative references runtime through Execution identifiers.

It does **not** own execution state.

---

## Initiative Structure

```
Initiative
├── Goal
├── Planning
│      ├── Epic
│      ├── Story
│      ├── Task
│      └── Dependencies
│
└── Runtime References
       ├── Execution IDs
       └── Active Execution
```

Planning remains stable.

Runtime evolves independently.

---

# Initiative Lifecycle

```
Draft
↓
Planning
↓
Ready
↓
Running
↓
Completed
↓
Archived
```

The lifecycle describes the business outcome.

It does **not** describe runtime execution.

---

# Planning Model

Planning is hierarchical.

```
Initiative
↓
Epic
↓
Story
↓
Task
```

Each level increases implementation detail.

---

## Epic

Represents a planning boundary.

Responsibilities:
- group Stories
- organize work
- prioritize delivery

Epics are implementation details.

Leaders primarily interact with Initiatives.

---

## Story

Represents a business deliverable.

Examples:
- Produce Architecture Proposal
- Write Promotion Document
- Build API Specification

Stories own Tasks.

Stories are visible on the planning board.

---

## Story Responsibilities

Stories define:
- objective
- acceptance criteria
- priority
- dependencies
- completion state

Stories do **not** execute.

Execution creates Story Executions.

---

## Task

Tasks represent planned work.

Tasks define:
- intent
- planning mode
- capability (optional)
- dependencies
- acceptance criteria

Tasks intentionally avoid describing implementation.

They describe **what should happen**, not **how it happens**.

---

# Planning Modes

Every Task has exactly one Planning Mode.

```
Planning Mode
├── Structured
└── Goal-Oriented
```

Regardless of planning mode, every task eventually produces the same runtime model.

---

## Structured Planning

The planner explicitly defines:
- capability
- dependencies
- acceptance criteria
- execution constraints

Example:

```
Task
Write README
Capability
Write Markdown
```

Structured planning is deterministic and recommended for production workflows.

---

## Goal-Oriented Planning

The planner specifies the desired outcome instead of the implementation.

Example:

```
Goal
Create a promotion document demonstrating technical leadership.
Success Criteria
Executive quality
Less than three pages
Ready for manager review
```

The AI Planner determines:
- capabilities
- execution order
- providers
- dependencies

before runtime begins.

The resulting execution is normalized into the same capability model as structured planning.

# Aggregate: Execution

Execution represents the runtime realization of planning.

Planning describes intent.

Execution records reality.

Unlike planning objects, Executions are disposable and repeatable.

The same Story may execute many times.

```
Story
↓
Execution #1
↓
Execution #2
↓
Execution #3
```

Each execution is completely independent.

---

## Execution Responsibilities

Execution owns:
- runtime status
- progress
- timeline
- capability executions
- human requests
- decisions
- artifacts
- metrics
- cost
- provider telemetry

Execution never modifies planning.

---

## Execution Structure

```
Execution
├── Story Reference
├── Status
├── Capability Executions
├── Timeline
├── Human Requests
├── Decisions
├── Artifacts
├── Metrics
└── Metadata
```

Execution is the primary runtime object monitored by leaders.

---

# Execution Lifecycle

```
Created
↓
Queued
↓
Running
↓
Waiting
↓
Completed
↓
Archived
```

Alternative terminal states

```
Cancelled
Failed
Expired
```

Only runtime changes state.

Planning objects remain unchanged.

---

# Capability Model

A Capability represents **what skill is required**.

Capabilities intentionally hide implementation details.

Examples

```
Research
Search
Write Markdown
Generate Diagram
Review
Summarize
Translate
Generate Code
Analyze
Test
Deploy
```

Capabilities are reusable across every Initiative.

---

## Capability Philosophy

Capabilities answer:

> What ability is required?

They do **not** answer:
- Which LLM?
- Which prompt?
- Which provider?
- Which workflow?

Those decisions belong to runtime.

---

## Capability Structure

```
Capability
id
name
description
category
inputs
outputs
supportedStrategies
supportedProviders
constraints
```

Capabilities should be completely reusable.

---

## Capability Categories

Suggested categories

```
Research
Authoring
Engineering
Review
Analysis
Visualization
Communication
Operations
Planning
Decision Support
```

Categories exist purely for discovery.

They have no runtime meaning.

---

# Capability Catalog

Every Workspace owns exactly one Capability Catalog.

```
Capability Catalog
├── Research
├── Search
├── Summarize
├── Write Markdown
├── Generate Diagram
├── Review
├── Analyze
├── Generate Code
├── Translate
├── Test
└── Deploy
```

The catalog enables:
- reuse
- governance
- versioning
- provider compatibility
- discovery

---

# Provider Model

Providers execute Capabilities.

Providers represent concrete implementations.

Examples

```
OpenAI
Anthropic
Google Gemini
Claude Code
Cursor
GitHub MCP
Slack MCP
Temporal Activity
Human
```

Providers are replaceable.

Capabilities remain stable.

---

## Provider Responsibilities

Providers are responsible only for execution.

They should never contain business rules.

Responsibilities
- execute work
- estimate cost
- estimate latency
- report progress
- expose telemetry
- return outputs

---

## Provider Contract

Every Provider should expose a common interface.

```
supports(capability)
estimate(request)
execute(request)
cancel(executionId)
resume(executionId)
health()
metadata()
```

This allows Providers to be swapped without affecting business logic.

---

# Execution Strategy

Execution Strategy defines **how a Capability should be executed**.

```
Capability
↓
Execution Strategy
↓
Provider
↓
Execution
```

Strategies coordinate Providers.

Providers perform work.

---

## Why Execution Strategy Exists

Without strategies:

```
Capability
↓
Provider
```

Every Provider would need to implement:
- retries
- parallelism
- consensus
- approval logic
- fan-out

This couples Providers with orchestration.

Instead:

```
Capability
↓
Strategy
↓
Provider
```

Providers stay simple.

Strategies remain reusable.

---

## Built-in Strategies

### Single Provider

```
Capability
↓
Claude
```

---

### Retry

```
Capability
↓
Claude
↓
Retry
↓
Retry
↓
Success
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

Results remain independent.

---

### Consensus

```
Capability
↓
Claude
GPT
Gemini
↓
Evaluator
↓
Final Result
```

Useful for:
- reviews
- evaluations
- ranking
- confidence improvement

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

Suitable for document generation.

---

### Human Review

```
Capability
↓
AI
↓
Human Approval
↓
Continue
```

Execution pauses automatically.

---

### Fan-Out

```
Capability
↓
Region A
Region B
Region C
↓
Merge
```

Supports large-scale parallel work.

---

### Loop Until Criteria

```
Generate
↓
Evaluate
↓
Satisfied?
↓
No
↓
Improve
↓
Evaluate
```

Terminates when acceptance criteria are met.

---

# Runtime Hierarchy

The complete runtime hierarchy is:

```
Execution
├── Capability Execution
│      ├── Provider Execution
│      ├── Provider Execution
│      └── Provider Execution
├── Timeline
├── Artifacts
├── Human Requests
├── Decisions
└── Metrics
```

Every level has exactly one responsibility.

This keeps runtime extensible while preserving a clean domain model.

---

# Capability Execution

Capability Execution represents one runtime invocation of a Capability.

Responsibilities
- receive inputs
- invoke Strategy
- collect Provider outputs
- evaluate completion
- publish Timeline events

A Capability may execute multiple Providers.

---

# Provider Execution

Provider Execution represents one concrete runtime invocation.

Example

```
Capability
Generate Diagram
↓
Claude
```

or

```
Capability
Research
↓
GitHub MCP
```

Provider Executions are implementation details.

They should rarely be surfaced in high-level UI.

---

# Execution Metadata

Every Execution records operational metadata.

```
Execution Metadata
executionId
startedAt
completedAt
duration
provider
strategy
cost
tokens
retries
status
parentExecution
correlationId
```

This data powers observability without affecting business behavior.

---

# Design Constraints

The following rules are mandatory.

1. Capabilities never reference Providers directly.
2. Providers never contain business logic.
3. Strategies orchestrate Providers.
4. Providers may be replaced without changing planning.
5. Every Capability Execution produces Timeline events.
6. Every Provider Execution records telemetry.
7. Execution metadata is immutable after completion.
8. Runtime objects never modify planning objects.

These constraints ensure that the execution engine can evolve independently of the planning model while maintaining a stable business domain.

# Human Interaction Model

Leader Control Center is fundamentally a **Human-in-the-Loop** platform.

AI performs execution.

Humans perform governance.

Unlike traditional workflow systems where humans are embedded as workflow steps, Leader Control Center models human interaction as explicit domain objects.

```
Execution
↓
Human Request
↓
Decision
↓
Continue Execution
```

This separation makes every human interaction observable, auditable and replayable.

---

# Human Request

A Human Request represents a runtime pause that requires human input.

The platform **never blocks silently**.

If execution cannot continue, it must create exactly one Human Request.

Examples:
- Approval
- Clarification
- Budget Approval
- Tool Permission
- Risk Acceptance
- Missing Information
- Choose Option
- Escalation

---

## Human Request Structure

```
Human Request
id
executionId
type
title
description
priority
requestedBy
requestedAt
deadline
status
decisionId
metadata
```

---

## Human Request Lifecycle

```
Created
↓
Pending
↓
Viewed
↓
Answered
↓
Closed
```

Alternative terminal states:

```
Expired
Cancelled
```

Human Requests are immutable after closure.

---

# Human Request Types

## Approval

The workflow proposes an action.

The human chooses whether to continue.

Examples
- Publish document
- Execute deployment
- Send email
- Merge PR

---

## Clarification

Execution lacks sufficient information.

Examples
- Missing project name
- Missing requirements
- Missing acceptance criteria

---

## Choice

Multiple execution paths are available.

Example

```
Continue with
○ Option A
○ Option B
○ Option C
```

The workflow cannot decide independently.

---

## Permission

Execution requires elevated access.

Examples
- GitHub permission
- Slack permission
- Google Drive access
- Internal API credentials

---

## Budget

Execution exceeds predefined limits.

Examples
- Estimated AI cost
- API cost
- Cloud execution cost

---

## Risk Acceptance

Execution detects elevated operational risk.

Examples
- Delete resources
- Production deployment
- Sensitive document generation

---

# Decisions

A Decision is the human response to a Human Request.

Every Human Request produces exactly one Decision.

No exceptions.

---

## Decision Structure

```
Decision
id
requestId
type
comment
attachments
createdBy
createdAt
```

---

## Decision Types

```
Approve
Reject
Continue
Abort
Clarify
Retry
Select Option
Delegate
```

Future decision types may be introduced without affecting runtime architecture.

---

# Human Responsibility Boundary

The platform intentionally separates human responsibilities from AI responsibilities.

## Humans

Responsible for:
- business goals
- priorities
- planning
- governance
- approvals
- exceptions
- strategic decisions

---

## AI

Responsible for:
- execution
- research
- document generation
- analysis
- coding
- reviews
- reporting

This separation is a core architectural principle.

---

# Artifact Model

Artifacts are first-class domain objects.

The purpose of execution is to produce Artifacts.

Everything else exists to support that objective.

---

## Artifact Philosophy

Traditional workflow engines produce logs.

Leader Control Center produces business assets.

Examples

```
Architecture Proposal
Promotion Document
Specification
Presentation
Diagram
Source Code
Spreadsheet
Knowledge Base
Migration Plan
```

Artifacts are durable business outputs.

---

## Artifact Structure

```
Artifact
id
initiativeId
storyId
executionId
type
name
version
status
createdAt
createdBy
contentReference
metadata
```

Artifacts reference content.

They do not necessarily store content.

This allows future integration with:
- Git
- Google Drive
- Notion
- S3
- SharePoint
- Local Storage

---

## Artifact Types

Suggested built-in types

```
Markdown
PDF
Presentation
Diagram
Spreadsheet
Code
Specification
Image
Text
JSON
```

Additional types may be registered by plugins.

---

## Artifact Lifecycle

```
Draft
↓
Generated
↓
Reviewed
↓
Approved
↓
Published
↓
Archived
```

Artifact lifecycle is independent from Execution lifecycle.

---

## Artifact Versioning

Artifacts are immutable.

Updates create new versions.

```
Architecture.md
v1
↓
v2
↓
v3
↓
v4
```

Previous versions remain accessible.

---

# Timeline

Every runtime object contributes events to the Timeline.

The Timeline is the single source of truth for execution history.

Nothing modifies history.

Everything appends history.

---

## Timeline Event Structure

```
Timeline Event
id
executionId
timestamp
type
actor
source
payload
```

---

## Event Sources

Events may originate from:

```
Human
Capability
Provider
Workflow Engine
System
Plugin
```

---

## Timeline Categories

Planning

```
Task Created
Task Updated
Dependency Added
```

Execution

```
Execution Started
Execution Completed
Execution Failed
```

Capability

```
Capability Started
Capability Completed
Capability Failed
```

Provider

```
Provider Invoked
Provider Retried
Provider Failed
```

Human

```
Approval Requested
Decision Received
Clarification Answered
```

Artifacts

```
Artifact Generated
Artifact Published
Artifact Approved
```

---

# Metrics

Metrics are runtime observations.

Metrics never influence business behavior.

Examples

```
Execution Duration
Capability Duration
Provider Latency
Retry Count
AI Cost
Token Usage
Human Wait Time
Artifact Count
```

Metrics exist for observability.

---

# Domain Relationships

The complete business model can be summarized as:

```
Workspace
└── Initiative
      ├── Planning
      │      ├── Epic
      │      ├── Story
      │      └── Task
      │
      └── Runtime
             ├── Execution
             │      ├── Capability Execution
             │      │      └── Provider Execution
             │      │
             │      ├── Human Requests
             │      ├── Decisions
             │      ├── Timeline
             │      ├── Metrics
             │      └── Artifacts
             │
             └── Attention Queue
```

This relationship intentionally separates:
- planning
- execution
- governance
- outputs
- observability

while keeping them connected through a stable business model.

---

# Domain Invariants

The following rules are mandatory and should be enforced regardless of implementation.

## Planning
- An Initiative owns planning.
- A Story belongs to exactly one Epic.
- A Task belongs to exactly one Story.
- Planning objects never contain runtime state.

---

## Runtime
- Every Execution belongs to exactly one Story.
- An Execution may invoke many Capabilities.
- A Capability Execution may invoke many Provider Executions.
- Runtime objects never modify planning.

---

## Human Interaction
- Every Human Request belongs to exactly one Execution.
- Every Human Request produces exactly one Decision.
- Closed Human Requests cannot be reopened.

---

## Artifacts
- Every Artifact has exactly one producing Execution.
- Artifacts are immutable.
- Every update creates a new version.

---

## Timeline
- Every runtime action produces at least one Timeline Event.
- Timeline Events are append-only.
- Timeline is the authoritative execution history.

---

# Summary

This domain model intentionally separates **business intent** from **technical implementation**.

Planning remains stable and business-oriented.

Runtime remains observable and replaceable.

Capabilities describe **what** work should be performed.

Strategies describe **how** work should be orchestrated.

Providers describe **who or what** performs the work.

This separation allows Leader Control Center to evolve from manually supervised AI workflows into increasingly autonomous systems without requiring changes to the core domain model.
