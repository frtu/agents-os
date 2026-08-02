# 07-workflow-engine.md

> **Purpose**
>
> This document defines the Workflow Engine abstraction used by Leader Control Center.
>
> The Workflow Engine is responsible for durable orchestration of Runtime execution.
>
> It is intentionally treated as an infrastructure component rather than part of the business domain.
>
> The Runtime Domain owns execution semantics.
> The Workflow Engine owns execution durability.

---

# Workflow Philosophy

Leader Control Center deliberately separates business execution from workflow orchestration.

```
Planning
↓
Runtime Domain
↓
Workflow Engine
↓
Infrastructure
```

The Runtime decides **what** should happen.

The Workflow Engine guarantees **that** it eventually happens.

---

# Core Principle

The Runtime must remain completely independent from any workflow technology.

This enables migration between engines without changing:
- Planning
- Runtime
- Capabilities
- API
- Frontend

The Workflow Engine becomes a replaceable implementation.

---

# Responsibilities

The Workflow Engine is responsible for:
- durable execution
- state persistence
- timers
- retries
- scheduling
- waiting
- signals
- execution history
- crash recovery
- deterministic replay

It is **not** responsible for:
- business decisions
- planning
- provider selection
- AI execution
- human governance
- capability definitions

---

# Architecture Position

```
                    API
                     │
               Runtime Domain
                     │
          Workflow Abstraction
                     │
             Workflow Adapter
                     │
          Temporal / Future Engine
                     │
            Infrastructure
```

Only the Workflow Adapter knows the concrete engine.

---

# Design Goals

The abstraction should provide:
- portability
- deterministic execution
- scalability
- observability
- durability
- fault tolerance

The abstraction should hide:
- SDKs
- engine terminology
- persistence mechanisms
- implementation APIs

---

# Workflow Abstraction

The Runtime communicates through a minimal contract.

```
Workflow Engine
start()
signal()
query()
cancel()
terminate()
await()
schedule()
resume()
```

Additional capabilities may be added without affecting the Runtime Domain.

---

# Workflow Lifecycle

Every execution follows the same lifecycle.

```
Created
↓
Scheduled
↓
Running
↓
Waiting
↓
Completed
```

Alternative terminal states

```
Cancelled
Failed
Timed Out
Terminated
```

The Runtime observes these states.

The engine implements them.

---

# Workflow Instance

Each Runtime Execution maps to one Workflow Instance.

```
Story Execution
↓
Workflow Instance
```

The mapping is implementation specific.

Business objects never reference workflow identifiers directly.

---

# Child Workflows

Large executions may be decomposed.

Example

```
Initiative Workflow
│
├── Story Workflow
├── Story Workflow
├── Story Workflow
└── Story Workflow
```

This improves:
- scalability
- fault isolation
- parallelism

The decomposition is invisible to Planning.

---

# Workflow Context

Every Workflow receives immutable context.

```
Execution ID
Planning Version
Workspace
Correlation ID
Configuration
Metadata
```

Workflow Context is infrastructure context.

Business state remains inside Runtime.

---

# Deterministic Execution

The Workflow Engine must support deterministic replay.

Execution logic must produce identical results when replayed using the same history.

Determinism enables:
- crash recovery
- upgrades
- replay
- debugging
- auditing

---

# Waiting

Long-running waiting is a first-class capability.

Examples

```
Human Approval
Timer
External Event
Webhook
Dependency
Business Deadline
```

Waiting should not consume compute resources.

---

# Timers

Timers are durable.

Examples

```
Retry After
Resume Tomorrow
Wait 30 Days
Deadline
Maintenance Window
```

Timers survive:
- deployment
- restart
- failover

---

# Signals

External systems communicate with workflows using Signals.

Examples

```
Approval Received
Permission Granted
Webhook Received
User Responded
Retry Requested
```

Signals are infrastructure events.

The Runtime translates them into business actions.

---

# Queries

Queries inspect workflow state.

Examples

```
Current Status
Waiting Reason
Pending Signals
Execution Metadata
```

Queries never modify workflow state.

---

# Cancellation

Cancellation is cooperative.

```
Cancel Requested
↓
Cleanup
↓
Cancelled
```

The Runtime determines business compensation.

The Workflow Engine performs orchestration.

---

# Replay

Replay reconstructs execution using durable history.

Replay should never:
- call providers
- send emails
- invoke webhooks
- perform irreversible actions

Replay exists for recovery and diagnostics.

---

# Engine Independence

The Runtime depends only on the abstraction.

Current implementation

```
Temporal
```

Potential future implementations

```
Azure Durable Functions
AWS Step Functions
Netflix Conductor
Google Workflows
Custom Engine
```

Changing engines should require only a new Workflow Adapter.

---

# Workflow Invariants

The Workflow subsystem guarantees:

## Durability
- Executions survive process failure.
- Waiting survives deployment.
- Timers survive restart.

---

## Determinism
- Replay is deterministic.
- Workflow history is immutable.
- Side effects are isolated.

---

## Isolation
- Business logic remains in Runtime.
- Providers remain outside the Workflow Engine.
- Planning never references workflow constructs.

---

## Portability
- Runtime depends only on the Workflow Abstraction.
- Engine-specific SDKs are isolated in the Adapter.
- Business terminology never includes workflow engine concepts.

---

# Mapping to Runtime

The Workflow Engine is a runtime implementation detail.

```
Planning
↓
Runtime Execution
↓
Workflow Instance
↓
Workflow Tasks
↓
Infrastructure
```

Planning never "creates a workflow."

Runtime never "executes an activity."

Instead, the Runtime requests durable execution, and the Workflow Engine fulfills that request through its own internal mechanisms.

This separation ensures that Leader Control Center remains technology-independent while benefiting from enterprise-grade workflow orchestration.

# Workflow Adapter

The Workflow Adapter is the only component that understands a specific workflow engine.

It translates the Runtime's workflow abstraction into engine-specific operations.

```
Runtime Domain
↓
Workflow Abstraction
↓
Workflow Adapter
↓
Workflow Engine
```

This isolates the Domain from infrastructure concerns.

---

# Design Principles

The Workflow Adapter must be:
- replaceable
- deterministic
- stateless where possible
- observable
- versionable
- engine-specific

The Runtime should never reference adapter classes directly.

---

# Adapter Responsibilities

The Adapter is responsible for:
- starting workflows
- delivering signals
- executing timers
- querying workflow state
- mapping retries
- managing child workflows
- workflow version compatibility

The Adapter is **not** responsible for:
- business decisions
- planning
- provider routing
- capability execution
- human approval logic

---

# Adapter Contract

Conceptually every adapter implements:

```
WorkflowAdapter
start()
resume()
signal()
query()
cancel()
terminate()
scheduleTimer()
createChild()
registerWorker()
```

The Runtime communicates exclusively through this contract.

---

# Engine Mapping

Example mapping

| Workflow Abstraction | Temporal | Future Engine |
|----------------------|----------|---------------|
| start() | StartWorkflow | StartExecution |
| signal() | SignalWorkflow | SendSignal |
| query() | QueryWorkflow | QueryExecution |
| scheduleTimer() | Sleep | Delay |
| createChild() | Child Workflow | Sub Workflow |
| cancel() | Cancel Workflow | Cancel Execution |

Only the adapter understands these mappings.

---

# Workflow Workers

Workflow execution is performed by Workers.

```
Workflow Engine
↓
Task Queue
↓
Worker
↓
Workflow Adapter
↓
Runtime
```

Workers host workflow implementations.

They never contain business rules.

---

# Task Queues

Task Queues provide execution isolation.

Example

```
planning
runtime
artifacts
notifications
providers
```

Task queue names are infrastructure configuration.

They never appear in Planning or Runtime.

---

# Workflow Definition

A workflow definition coordinates Runtime execution.

Example

```
Workflow
↓
Initialize
↓
Schedule Capability
↓
Wait
↓
Resume
↓
Complete
```

Workflow definitions remain intentionally thin.

Business behavior belongs in Runtime Services.

---

# Activities

Activities execute short-lived infrastructure work.

Examples

```
Persist State
Call Provider
Publish Event
Read Configuration
Invoke Webhook
```

Activities should be:
- idempotent
- retryable
- stateless where practical

Activities are implementation details.

The Runtime models only Capability Execution.

---

# Signals

Signals communicate asynchronous events.

Examples

```
Human Approved
Webhook Received
Timer Triggered
External Event
Retry Requested
```

The Adapter converts Signals into Runtime events.

---

# Signal Routing

```
External Event
↓
Workflow Adapter
↓
Workflow Instance
↓
Runtime Event
↓
Execution
```

Signals should never bypass Runtime validation.

---

# Queries

Queries inspect workflow state.

Typical mappings

```
Execution Status
Current Wait State
Pending Timers
Workflow Metadata
```

Queries are read-only.

They should not trigger execution.

---

# Timers

The Adapter exposes durable timers through the abstraction.

Example

```
Runtime
↓
scheduleTimer()
↓
Workflow Engine Timer
↓
Resume Execution
```

Timer implementation is engine-specific.

---

# Child Workflows

Large executions may be decomposed into child workflows.

```
Story Workflow
↓
Research
↓
Writing
↓
Review
```

The Runtime decides when decomposition occurs.

The Adapter creates the appropriate engine objects.

---

# Retry Mapping

Retries are coordinated by Runtime Strategies.

The Adapter configures engine retry behavior.

Example

```
Capability
↓
Retry Strategy
↓
Workflow Retry Policy
```

Business retry semantics remain outside the workflow engine.

---

# Side Effects

Some operations are irreversible.

Examples

```
Send Email
Deploy Service
Create Ticket
Charge Credit Card
```

Side effects must execute through Activities or Provider adapters.

Workflow replay must never repeat irreversible operations.

---

# Deterministic Constraints

Workflow implementations must avoid non-deterministic behavior.

Examples of prohibited behavior inside workflow logic:

```
Random()
Current Time
Network Calls
Database Queries
UUID Generation
```

Instead, these values are obtained through Activities or deterministic engine APIs.

---

# Versioning

Workflow definitions evolve over time.

The Adapter must support:
- running historical workflows
- introducing new workflow logic
- safe upgrades
- rollback

Existing executions should continue uninterrupted.

---

# Workflow Upgrades

Upgrade strategy

```
Workflow v1
↓
Continue Running
↓
Workflow v2
↓
New Executions
```

Historical executions should not automatically migrate.

---

# Failure Handling

Workflow infrastructure failures include:

```
Worker Crash
Engine Restart
Lost Connection
Task Timeout
Deployment
Infrastructure Failure
```

The engine guarantees recovery.

The Runtime guarantees business correctness.

---

# Observability

The Adapter publishes infrastructure telemetry.

Examples

```
Workflow Started
Workflow Completed
Workflow Failed
Timer Scheduled
Signal Delivered
Worker Registered
```

Infrastructure events complement, but never replace, Runtime Timeline Events.

---

# Adapter Invariants

The Workflow Adapter enforces the following rules.

## Isolation
- Runtime communicates only through the Workflow Abstraction.
- Engine SDKs never leak into Domain code.
- Workflow identifiers remain infrastructure details.

---

## Determinism
- Workflow logic is deterministic.
- Side effects execute outside replayable workflow code.
- Activities encapsulate irreversible operations.

---

## Compatibility
- Historical executions continue using compatible workflow definitions.
- Adapter changes do not require Planning or Runtime changes.
- New workflow engines implement the same abstraction.

---

## Observability
- Infrastructure telemetry is published independently of business events.
- Correlation IDs propagate through the adapter.
- Every workflow instance can be traced back to its Runtime Execution.

By isolating engine-specific behavior within the Workflow Adapter, Leader Control Center achieves portability across workflow technologies while preserving a stable business-oriented Runtime model.

# Workflow Execution Model

The Workflow Engine provides durable orchestration for Runtime execution.

The Runtime defines execution semantics.

The Workflow Engine guarantees reliable progression through those semantics.

```
Planning Graph
↓
Runtime Scheduler
↓
Workflow Instance
↓
Capability Execution
↓
Completion
```

Workflow execution is an implementation of the Runtime model, not the business model itself.

---

# Execution Topology

Leader Control Center uses hierarchical workflow composition.

```
Initiative Workflow
│
├── Story Workflow
│      │
│      ├── Capability Workflow
│      ├── Capability Workflow
│      └── Capability Workflow
│
└── Story Workflow
```

This mirrors the Runtime hierarchy while remaining invisible to API consumers.

---

# Parent Responsibilities

The parent workflow coordinates execution.

Responsibilities include:
- lifecycle management
- dependency scheduling
- child orchestration
- progress aggregation
- cancellation propagation
- timeout propagation

The parent should never execute provider logic.

---

# Child Responsibilities

Child workflows own isolated execution.

Typical responsibilities include:
- Capability scheduling
- waiting
- retries
- compensation
- completion reporting

Child workflows communicate only through the Workflow Adapter.

---

# Dependency Scheduling

Execution order is derived from the Planning Graph.

```
Capability A
↓
Capability B
↓
Capability C
```

Independent nodes may execute concurrently.

The scheduler continuously evaluates the dependency graph.

---

# Parallel Execution

The Runtime may schedule multiple executable nodes simultaneously.

Example

```
Research
Documentation
Architecture Diagram
↓
Merge Results
↓
Publish
```

Parallelism is a scheduling decision.

It is not encoded inside individual workflows.

---

# Waiting Model

Waiting is treated as durable suspension.

Waiting conditions include:

```
Human Approval
External Event
Webhook
Timer
Business Deadline
Dependency Completion
```

While waiting:
- workflow state is persisted
- compute resources are released
- execution remains observable

---

# Continue-As-New

Long-running executions may accumulate extensive workflow history.

The Workflow Engine may periodically create a new execution while preserving business continuity.

```
Workflow
↓
History Threshold
↓
Continue-As-New
↓
Workflow
```

The Runtime observes a single continuous Execution.

Workflow segmentation is hidden.

---

# Workflow History

Workflow history is infrastructure state.

Typical events include:

```
Workflow Started
Activity Scheduled
Signal Received
Timer Fired
Child Started
Workflow Completed
```

Workflow history complements—but does not replace—the Runtime Timeline.

The Runtime Timeline remains the business source of truth.

---

# Saga Pattern

Business processes often span multiple external systems.

The Runtime models these as Sagas.

```
Capability A
↓
Capability B
↓
Capability C
```

If execution fails:

```
Compensation C
↓
Compensation B
↓
Compensation A
```

Compensation behavior is defined by Runtime Strategies.

The Workflow Engine coordinates execution only.

---

# Compensation Workflow

Compensation is executed explicitly.

```
Failure
↓
Compensation Strategy
↓
Compensation Capability
↓
Completed
```

Rollback behavior should remain observable.

Compensation is never implicit.

---

# Timeout Management

Timeouts exist at multiple levels.

```
Workflow Timeout
Story Timeout
Capability Timeout
Provider Timeout
Human Response Timeout
```

Each timeout is independently configurable.

Timeouts generate Runtime events.

---

# Cancellation Propagation

Cancellation flows hierarchically.

```
Initiative
↓
Story
↓
Capability
↓
Provider
```

Every level receives an opportunity to perform cleanup.

Cancellation remains cooperative whenever possible.

---

# Failure Isolation

Failures should remain localized.

```
Story A
Failed
Story B
Running
Story C
Completed
```

One failed Story should not automatically terminate unrelated execution.

Propagation rules are defined by Runtime policies.

---

# Scaling Model

Workflow execution is horizontally scalable.

Workers may be added or removed without affecting business execution.

```
Task Queue
↓
Worker A
Worker B
Worker C
Worker D
```

Scaling decisions are operational concerns.

---

# Queue Partitioning

Task queues may be partitioned.

Examples

```
workspace-a
workspace-b
high-priority
low-priority
providers
artifacts
```

Partitioning strategies should remain configurable.

Planning and Runtime remain unaware of queue topology.

---

# High Availability

Workflow infrastructure should tolerate:
- worker failures
- process crashes
- node failures
- rolling deployments
- regional failover

Business execution should continue without user intervention.

---

# Disaster Recovery

Recovery objectives include:

```
Durable State
Replay
Worker Replacement
Workflow Recovery
Execution Continuity
```

Recovery procedures should not require rebuilding Planning or Runtime state.

---

# Performance Considerations

Workflow implementations should optimize for:
- deterministic replay
- minimal workflow state
- coarse-grained activities
- bounded workflow history
- efficient signaling
- scalable task queues

Business correctness always takes priority over optimization.

---

# Operational Guidelines

Recommended practices:
- keep workflow code thin
- move business logic into Runtime services
- use child workflows for isolation
- prefer explicit compensation
- emit business events independently
- bound retry policies
- bound workflow history growth

Avoid embedding provider logic directly in workflows.

---

# Workflow Metrics

Infrastructure metrics include:

```
Running Workflows
Workflow Latency
Workflow History Size
Task Queue Depth
Worker Utilization
Signal Throughput
Timer Count
Continue-As-New Count
Replay Duration
```

These metrics are operational.

They complement Runtime business metrics.

---

# Workflow Invariants

The Workflow Engine guarantees the following.

## Execution
- Every Runtime Execution maps to one active Workflow Instance.
- Child workflows are implementation details.
- Dependency scheduling follows the Planning Graph.

---

## Durability
- Waiting is durable.
- Timers survive failures.
- Execution resumes after infrastructure recovery.

---

## Isolation
- Workflow failures are isolated whenever possible.
- Compensation is explicit.
- Business state is owned by Runtime, not workflow history.

---

## Scalability
- Workers scale horizontally.
- Queue topology is configurable.
- Continue-As-New is transparent to the business domain.

---

## Separation of Concerns
- Runtime defines business execution.
- Workflow Engine guarantees durability.
- Workflow Adapter isolates implementation.
- Providers execute work.

These architectural boundaries ensure that workflow orchestration remains a robust infrastructure capability while preserving the long-term independence and evolution of the business domain.

# Workflow Engine Service Provider Interface (SPI)

The Workflow Engine integrates with the Runtime through a Service Provider Interface (SPI).

The SPI defines the minimum capabilities required by Leader Control Center.

```
Runtime
↓
Workflow SPI
↓
Workflow Adapter
↓
Workflow Engine
```

The SPI is intentionally small and stable.

---

# SPI Responsibilities

The Workflow SPI enables the Runtime to:
- create executions
- resume executions
- pause executions
- cancel executions
- query execution state
- wait for events
- schedule timers
- execute child workflows
- publish execution events

Everything else is considered engine-specific.

---

# SPI Contract

Conceptually, every Workflow Engine implements:

```
WorkflowEngine
startExecution()
resumeExecution()
pauseExecution()
cancelExecution()
terminateExecution()
sendSignal()
queryExecution()
scheduleTimer()
createChildExecution()
registerWorkers()
```

Implementations may expose additional capabilities, but the Runtime only depends on this contract.

---

# Engine Capability Matrix

The Workflow SPI defines expected capabilities rather than implementation details.

| Capability | Required | Notes |
|------------|----------|------|
| Durable Execution | ✅ | Mandatory |
| Timers | ✅ | Mandatory |
| Signals | ✅ | Mandatory |
| Queries | ✅ | Mandatory |
| Child Workflows | ✅ | Preferred |
| Continue-As-New | Optional | Recommended |
| Workflow Versioning | Optional | Recommended |
| Cron Scheduling | Optional | May remain outside Runtime |
| Search Attributes | Optional | Infrastructure optimization |

The Runtime should degrade gracefully when optional features are unavailable.

---

# Temporal Mapping (Reference)

The current implementation maps naturally to Temporal concepts.

| Runtime Concept | Temporal Concept |
|-----------------|------------------|
| Runtime Execution | Workflow Execution |
| Execution Strategy | Workflow Logic |
| Capability Execution | Activity Invocation |
| Human Wait | Signal + Await |
| Timer | Sleep |
| Child Execution | Child Workflow |
| Timeline Event | Workflow/Event History + Domain Events |

These mappings are informative only.

They are **not** part of the public architecture.

---

# Workflow State Ownership

State ownership is intentionally separated.

```
Planning
↓
Planning State
Runtime
↓
Business Execution State
Workflow Engine
↓
Durable Execution State
```

The Workflow Engine should never become the source of truth for business state.

---

# Runtime vs Workflow History

The platform maintains two complementary histories.

## Runtime Timeline

Business history.

Examples

```
Story Started
Capability Completed
Artifact Published
Approval Received
```

---

## Workflow History

Infrastructure history.

Examples

```
Workflow Started
Activity Scheduled
Signal Delivered
Timer Fired
```

Users primarily interact with the Runtime Timeline.

Workflow History is an operational artifact.

---

# Testing Strategy

Workflow implementations should be tested at multiple levels.

## Unit Tests

Validate:
- workflow decisions
- adapter behavior
- deterministic execution

No infrastructure required.

---

## Integration Tests

Validate:
- workflow engine integration
- timers
- signals
- retries
- child workflows

Infrastructure is required.

---

## End-to-End Tests

Validate:

```
Planning
↓
Runtime
↓
Workflow
↓
Providers
↓
Artifacts
```

These tests ensure architectural correctness.

---

# Local Development

Developers should be able to run the platform locally.

Recommended setup

```
Frontend
↓
API
↓
Runtime
↓
Local Workflow Engine
↓
Local Database
```

The development environment should closely mirror production while minimizing operational complexity.

---

# Deployment Strategy

Workflow workers should support rolling deployments.

```
Version N
↓
Version N + 1
↓
Drain Workers
↓
Upgrade
↓
Resume Processing
```

Active executions should continue without interruption.

---

# Workflow Migration

Historical executions should remain executable.

Migration strategy

```
Existing Executions
↓
Existing Workflow Definition
New Executions
↓
New Workflow Definition
```

Migration should be explicit rather than automatic.

---

# Operational Governance

Organizations should define operational policies.

Examples

```
Maximum Workflow Duration
Maximum Retry Count
Maximum Child Depth
Maximum Timer Duration
Allowed Workflow Versions
```

These policies are enforced outside business logic.

---

# Failure Recovery

Recovery procedures should support:
- worker replacement
- workflow replay
- infrastructure restart
- disaster recovery
- regional failover

Recovery should preserve execution identity and business continuity.

---

# Observability

Every workflow contributes operational telemetry.

Collected information includes:

```
Workflow Start
Workflow Completion
Workflow Failure
Replay Count
History Size
Queue Latency
Worker Health
Signal Throughput
Timer Count
```

Operational telemetry complements Runtime business metrics.

---

# Design Guidelines

Workflow implementations should:
- remain deterministic
- be infrastructure-focused
- delegate business behavior to Runtime
- isolate provider interactions
- prefer composition over complexity
- minimize workflow state

Workflow implementations should not:
- contain business policies
- make provider decisions
- manipulate Planning
- expose engine terminology through the API
- persist business entities directly

---

# Reference Architecture

```
                    Planning
                        │
                        ▼
                 Runtime Domain
                        │
                        ▼
                Workflow SPI
                        │
                        ▼
              Workflow Adapter
                        │
        ┌───────────────┴───────────────┐
        │                               │
   Temporal Engine               Future Engine
        │                               │
        └───────────────┬───────────────┘
                        ▼
               Durable Execution
                        │
                        ▼
                 Provider Layer
                        │
                        ▼
                 External Systems
```

The Workflow Engine is replaceable without changing the Planning, Runtime, API, or Capability layers.

---

# Workflow Design Checklist

Before introducing a new workflow, verify:
- Is this orchestration rather than business logic?
- Is the workflow deterministic?
- Are irreversible side effects isolated?
- Can execution survive restarts?
- Are waits implemented durably?
- Are retries bounded?
- Are child workflows justified?
- Are Timeline events emitted by the Runtime?
- Can the workflow be upgraded safely?
- Can the workflow be replayed safely?

---

# Workflow Invariants

The Workflow subsystem guarantees the following architectural rules.

## Architecture
- Runtime owns business execution.
- Workflow Engine owns durable orchestration.
- Workflow Adapter isolates engine-specific behavior.

---

## Durability
- Executions survive infrastructure failures.
- Waiting is durable.
- Timers persist across deployments.

---

## Determinism
- Workflow logic is replay-safe.
- Side effects occur outside replayable code.
- Historical executions remain reproducible.

---

## Portability
- Runtime depends only on the Workflow SPI.
- Engine implementations remain interchangeable.
- Public APIs never expose workflow-engine concepts.

---

## Observability
- Business events are published through the Runtime Timeline.
- Infrastructure telemetry remains separate.
- Every execution is fully traceable through correlation identifiers.

---

# Workflow Summary

The Workflow Engine is the durable orchestration backbone of Leader Control Center.

By introducing a stable Workflow SPI and isolating engine-specific behavior behind adapters, the platform gains enterprise-grade reliability while preserving a clean separation between business execution and infrastructure.

This architecture allows the platform to leverage powerful workflow engines such as Temporal today while remaining free to adopt alternative implementations in the future without impacting Planning, Runtime, Capabilities, or the public API.
