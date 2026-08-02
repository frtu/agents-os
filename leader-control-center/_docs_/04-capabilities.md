# 04-capabilities.md

> **Purpose**
>
> This document defines the Capability Model of Leader Control Center.
>
> Capabilities are the business abstraction that decouple planning from implementation.
>
> They represent **what work should be performed**, independent of:
>
> - AI providers
> - Workflow engines
> - MCP servers
> - APIs
> - Humans
> - External systems
>
> Every execution in the platform ultimately occurs through Capabilities.

---

# Capability Philosophy

Capabilities are the heart of the platform.

They are analogous to:

| Platform              | Equivalent |
| --------------------- | ---------- |
| Kubernetes            | Resource   |
| Temporal              | Activity   |
| Unix                  | Command    |
| AWS                   | Lambda     |
| Spring                | Bean       |
| Leader Control Center | Capability |

Unlike those systems, Capabilities are expressed in **business language**, not technical language.

---

# Core Principle

The platform deliberately separates **five different concerns**.

```
Planning
↓
Capability
↓
Strategy
↓
Provider
↓
Infrastructure
```

Each layer answers a different question.

| Layer          | Question                         |
| -------------- | -------------------------------- |
| Planning       | What should happen?              |
| Capability     | What business skill is required? |
| Strategy       | How should it be executed?       |
| Provider       | Who performs the work?           |
| Infrastructure | Where does it run?               |

No layer should leak into another.

---

# What is a Capability?

A Capability represents a reusable business skill.

Examples

```
Research
Search Documentation
Generate Markdown
Generate Diagram
Review Document
Summarize
Translate
Analyze Code
Generate Test Cases
Create Presentation
Deploy Service
```

Capabilities should be understandable without knowing anything about AI.

---

# Capability Characteristics

A Capability must be:
- reusable
- composable
- deterministic (where possible)
- provider-independent
- versioned
- discoverable
- observable
- testable

Capabilities should contain business behavior, not provider behavior.

---

# Capability Responsibilities

A Capability is responsible for:
- defining inputs
- defining outputs
- defining constraints
- declaring supported strategies
- declaring supported providers
- exposing metadata

A Capability is **not** responsible for:
- orchestration
- retries
- provider selection
- persistence
- scheduling
- workflow execution

---

# Capability Structure

```
Capability
id
name
displayName
description
category
version
status
owner
inputs
outputs
constraints
supportedStrategies
supportedProviders
metadata
```

The structure intentionally resembles an API contract.

---

# Capability Categories

Capabilities are grouped into logical domains.

Suggested built-in categories

```
Research
Authoring
Engineering
Analysis
Review
Visualization
Communication
Planning
Operations
Knowledge
Automation
Integration
```

Categories improve discoverability only.

They have no runtime semantics.

---

# Capability Identity

Every Capability has a globally unique identifier.

Example

```
capability.markdown.generate
capability.diagram.mermaid
capability.document.review
capability.code.analyze
```

Identifiers should remain stable across versions.

---

# Capability Naming

Names should express business intent.

Good

```
Generate Markdown
Review Architecture
Analyze Repository
Search Documentation
Deploy Application
```

Poor

```
GPT Writer
Claude Review
Call Activity
Invoke MCP
Execute Prompt
```

Capabilities should never expose implementation.

---

# Capability Versioning

Capabilities evolve independently.

```
Generate Markdown
v1
↓
v2
↓
v3
```

Planning references a Capability identifier.

Runtime resolves the appropriate version.

---

# Capability Lifecycle

```
Draft
↓
Experimental
↓
Active
↓
Deprecated
↓
Archived
```

Only Active versions are available for new planning.

Existing executions remain reproducible.

---

# Capability Registry

Every Workspace owns a Capability Registry.

```
Workspace
↓
Capability Registry
├── Research
├── Markdown
├── Diagram
├── Review
├── Translate
├── Analyze
└── Deploy
```

The Registry is the authoritative catalog of business skills.

---

# Registry Responsibilities

The Registry provides:
- discovery
- version resolution
- compatibility validation
- provider mapping
- governance
- documentation

The Runtime Engine never scans plugins directly.

It always queries the Registry.

---

# Capability Metadata

Metadata enriches Capabilities without affecting behavior.

Examples

```
Owner
Documentation URL
Examples
Tags
Estimated Cost
Estimated Duration
Risk Level
Compliance Flags
Security Classification
```

Metadata should remain descriptive.

Business behavior belongs elsewhere.

---

# Capability Discovery

Capabilities must be discoverable.

Users should be able to search by:
- name
- category
- tags
- owner
- input type
- output type

Example

```
Search
"diagram"
↓
Generate Mermaid
Generate PlantUML
Generate Draw.io
```

Discovery should prioritize business language over technical terminology.

---

# Capability Documentation

Every Capability should provide documentation.

Recommended sections

```
Overview
Inputs
Outputs
Examples
Supported Strategies
Supported Providers
Constraints
Version History
Owner
```

Documentation is part of the Capability contract.

---

# Capability Visibility

Capabilities may have different visibility levels.

```
Public
Workspace
Team
Private
Experimental
```

Visibility controls discovery, not execution.

Execution authorization is handled separately.

---

# Capability Invariants

The following rules always apply.

1. Every Capability has one stable identifier.
2. Every Capability belongs to one Category.
3. Every Capability declares Inputs and Outputs.
4. Capabilities never reference Providers directly.
5. Capabilities never contain orchestration logic.
6. Capabilities remain reusable across all Initiatives.
7. Capabilities are versioned independently of Planning.
8. Capabilities are immutable once published.

These invariants establish Capabilities as the stable business contract between Planning and Runtime.

# Capability SDK

The Capability SDK defines the contract between business capabilities and the Runtime Engine.

It provides a stable programming model that remains independent of:
- AI providers
- Workflow engines
- Programming languages
- Deployment models

The SDK exists so developers implement **business capabilities**, not infrastructure.

---

# Design Goals

The SDK should be:
- strongly typed
- deterministic
- composable
- testable
- observable
- provider-independent
- language-neutral

A Capability should be implementable in Python today and another language tomorrow without changing the business model.

---

# Capability Contract

Every Capability implements the same conceptual contract.

```
Capability
↓
Validate Inputs
↓
Prepare Context
↓
Execute
↓
Validate Outputs
↓
Publish Artifacts
↓
Return Result
```

The Runtime Engine owns orchestration.

The Capability owns business behavior.

---

# Capability Interface

Conceptually, every Capability implements:

```
Capability
initialize()
validate()
execute()
complete()
cleanup()
```

Additional optional lifecycle hooks may exist.

The Runtime Engine guarantees lifecycle ordering.

---

# Execution Context

Capabilities execute within a Runtime Context.

The Runtime injects this context automatically.

```
Execution Context
executionId
initiativeId
storyId
taskId
capabilityId
workspaceId
planningVersion
runtimeMetadata
```

Capabilities never construct this context themselves.

---

# Context Responsibilities

The Execution Context provides read-only access to:
- planning information
- runtime metadata
- execution identifiers
- configuration
- capabilities available in the workspace

The Context should never expose provider implementation details.

---

# Input Model

Every Capability defines an explicit Input Schema.

Example

```
Generate Markdown
Inputs
Title
Outline
Audience
References
Template
```

Inputs are immutable.

---

# Input Schema

Each input defines:

```
name
type
required
default
description
validation
```

Input schemas are versioned together with the Capability.

---

# Type System

The platform defines a common type system.

Primitive types

```
String
Integer
Boolean
Number
Date
DateTime
Duration
URI
```

Structured types

```
Object
List
Map
Enum
```

Domain types

```
Artifact
Decision
Human Request
Planning Graph
Execution Reference
Capability Output
```

The Runtime validates all types before execution.

---

# Output Model

Capabilities explicitly declare their outputs.

Outputs should be structured whenever possible.

Example

```
Markdown
Diagram
Review Report
JSON
Spreadsheet
Presentation
```

Outputs become inputs for downstream Capabilities.

---

# Output Schema

Outputs follow the same schema model as inputs.

```
Output
name
type
description
required
```

This enables static validation and composition.

---

# Validation

Validation occurs before execution.

Validation includes:
- required fields
- type compatibility
- business constraints
- schema compatibility

Invalid Capabilities never execute.

---

# Constraint Model

Capabilities may declare execution constraints.

Examples

```
Internet Required
Human Approval Required
Read Only
Internal Documents Only
Maximum Runtime
Maximum Cost
```

Constraints influence Runtime behavior without coupling the Capability to implementation.

---

# Configuration

Capabilities may expose configurable parameters.

Examples

```
Temperature
Creativity
Maximum Pages
Language
Tone
Output Format
```

Configuration is distinct from business inputs.

Inputs describe the work.

Configuration describes execution preferences.

---

# Default Configuration

Capabilities should provide sensible defaults.

Example

```
Generate Markdown
Language
English
Maximum Pages
10
Tone
Professional
```

Defaults improve usability while remaining overridable.

---

# Capability Context Services

Capabilities may access Runtime services through well-defined interfaces.

Examples

```
Artifact Service
Knowledge Service
Capability Registry
Configuration Service
Metrics Service
Logging Service
```

Capabilities should never instantiate infrastructure services directly.

---

# Artifact Access

Artifacts are exchanged through references rather than raw files.

```
Capability
↓
Artifact Reference
↓
Artifact Service
↓
Content
```

This avoids unnecessary duplication and supports external storage systems.

---

# Artifact References

Example

```
Artifact
id
type
version
location
checksum
```

The Runtime resolves references transparently.

---

# Capability Composition

Capabilities should be small and composable.

Instead of one large Capability:

```
Generate Proposal
```

Prefer:

```
Research
↓
Generate Outline
↓
Write Markdown
↓
Review
↓
Generate PDF
```

Small Capabilities maximize reuse.

---

# Nested Capabilities

A Capability may invoke another Capability through the Runtime.

```
Capability
↓
Capability
↓
Capability
```

The Runtime records each invocation independently.

Nested execution must remain observable.

---

# Capability Reuse

Capabilities are designed to be reusable across:
- Initiatives
- Stories
- Workspaces
- Organizations

A Capability should never assume knowledge of a specific project.

---

# Error Model

Capabilities report structured errors.

Example categories

```
Validation Error
Business Error
Temporary Failure
Dependency Failure
Configuration Error
Unexpected Error
```

The Runtime decides how to recover.

Capabilities only report facts.

---

# Testing

Every Capability should support isolated testing.

Recommended test categories

```
Input Validation
Business Logic
Output Validation
Failure Handling
Schema Compatibility
```

Capabilities should be testable without requiring a Workflow Engine or AI Provider.

---

# Capability Invariants

The SDK enforces the following rules.

1. Inputs are immutable.
2. Outputs conform to the declared schema.
3. Validation occurs before execution.
4. Capabilities never orchestrate other Capabilities directly.
5. Infrastructure is accessed only through Runtime services.
6. Capabilities never manage retries or scheduling.
7. Nested executions are recorded by the Runtime.
8. Business logic remains independent of Providers and Workflow Engines.

These invariants ensure that Capabilities remain portable, reusable, and maintainable while forming the stable execution contract of Leader Control Center.

# Capability Registry

The Capability Registry is the authoritative catalog of every Capability available within a Workspace.

It acts as the bridge between Planning, Runtime and the Plugin ecosystem.

```
Workspace
↓
Capability Registry
↓
Capabilities
↓
Runtime
```

Neither Planning nor Runtime should scan plugins directly.

Everything is resolved through the Registry.

---

# Registry Responsibilities

The Registry is responsible for:
- discovery
- version resolution
- dependency validation
- capability metadata
- plugin registration
- compatibility checks
- governance
- lifecycle management

The Registry never executes Capabilities.

---

# Registry Architecture

```
Workspace
↓
Registry
├── Capabilities
├── Plugins
├── Versions
├── Policies
├── Providers
└── Integrations
```

Each component has a distinct responsibility.

---

# Plugin Philosophy

Capabilities are distributed as Plugins.

A Plugin is a deployment package.

A Capability is a business abstraction.

One Plugin may expose:
- one Capability
- multiple Capabilities
- supporting assets

Example

```
Markdown Plugin
├── Generate Markdown
├── Review Markdown
├── Export PDF
```

---

# Plugin Structure

```
Plugin
id
name
publisher
version
description
license
status
capabilities
dependencies
metadata
```

Plugins are infrastructure.

Capabilities remain business objects.

---

# Plugin Lifecycle

```
Installed
↓
Validated
↓
Registered
↓
Active
↓
Deprecated
↓
Removed
```

Removal never affects completed executions.

---

# Capability Manifest

Every Plugin exposes a manifest.

The manifest is the Runtime contract.

Example

```
Plugin Manifest
Plugin Metadata
Capabilities
Input Schemas
Output Schemas
Strategies
Providers
Permissions
Dependencies
Configuration
```

The Runtime never inspects implementation code.

It consumes only the manifest.

---

# Capability Manifest

Each Capability defines its own manifest.

```
Capability Manifest
id
version
category
inputs
outputs
constraints
supportedStrategies
supportedProviders
documentation
examples
```

The manifest is immutable for a published version.

---

# Dynamic Registration

Plugins register Capabilities dynamically.

```
Plugin
↓
Registry
↓
Validation
↓
Registration
↓
Available
```

Registration occurs once.

Execution resolves from the Registry.

---

# Registry Validation

During registration the Registry validates:
- duplicate identifiers
- schema compatibility
- version conflicts
- dependency graph
- permission declarations
- configuration schema

Invalid Plugins are rejected.

---

# Dependency Model

Plugins may depend on other Plugins.

```
Plugin A
↓
Plugin B
↓
Plugin C
```

Dependency resolution occurs during registration.

Not during execution.

---

# Capability Dependencies

Capabilities should remain independent whenever possible.

When dependencies exist they should reference business contracts.

Example

```
Generate PDF
↓
Generate Markdown
```

They should never reference Provider implementations.

---

# Version Resolution

The Registry resolves compatible versions.

Planning references a stable Capability identifier.

```
Generate Markdown
↓
Registry
↓
v3.2.1
```

Runtime always executes a resolved version.

Planning remains unchanged.

---

# Version Compatibility

Versioning follows semantic compatibility.

```
Major
Breaking
Minor
Backward Compatible
Patch
Bug Fix
```

Existing Planning Versions continue using compatible Runtime versions unless explicitly migrated.

---

# Capability Discovery

Capabilities may be discovered by:

```
Name
Category
Tag
Owner
Input Type
Output Type
Plugin
Publisher
Visibility
```

Discovery should prioritize business language.

---

# Capability Search Example

```
Search
"review"
↓
Review Markdown
Review Architecture
Review Code
Review Specification
```

The Registry should support fuzzy search and tagging.

---

# Plugin Permissions

Plugins declare required permissions.

Examples

```
Filesystem
Internet
GitHub
Slack
Google Drive
Databases
Internal APIs
```

Permissions are explicit.

No Plugin receives implicit access.

---

# Capability Permissions

Capabilities inherit Plugin permissions.

Additional runtime permissions may be requested through Human Requests.

Example

```
Capability
↓
GitHub Permission
↓
Human Approval
↓
Execution
```

Permissions become part of the audit trail.

---

# MCP Integration

Model Context Protocol (MCP) servers are treated as Providers.

```
Capability
↓
Strategy
↓
MCP Provider
↓
MCP Server
```

The Capability remains unaware of MCP implementation details.

---

# External Systems

External integrations are modeled consistently.

Examples

```
GitHub
Slack
Google Drive
Notion
Jira
Confluence
Databricks
REST APIs
```

Each integration is exposed through a Provider implementation.

---

# Security Model

Plugins execute within a controlled Runtime environment.

Security objectives:
- least privilege
- explicit permissions
- execution isolation
- auditability
- reproducibility

Capabilities should never bypass Runtime security.

---

# Governance

Organizations may define governance policies.

Examples

```
Only approved Plugins
Signed Plugins
Trusted Publishers
Approved Categories
Restricted Capabilities
```

The Registry enforces these policies during registration.

---

# Registry Events

The Registry publishes immutable events.

Examples

```
Plugin Installed
Plugin Removed
Capability Registered
Capability Deprecated
Version Published
Permission Updated
```

These events enable auditing and synchronization.

---

# Registry Queries

Examples

```
List Capabilities
Find Capability
Resolve Version
List Plugins
List Providers
Search Categories
Search Tags
```

Queries never modify Registry state.

---

# Registry Invariants

The Capability Registry enforces the following rules.

## Plugins
- Every Plugin has one globally unique identifier.
- Plugins declare all Capabilities explicitly.
- Plugin dependencies must resolve successfully.

---

## Capabilities
- Every Capability belongs to exactly one Plugin.
- Capability identifiers are globally unique.
- Published manifests are immutable.

---

## Versioning
- Versions are immutable once published.
- Runtime resolves versions through the Registry.
- Planning never references implementation versions directly.

---

## Security
- All permissions are declared explicitly.
- Runtime validates permissions before execution.
- Human approval may be required for elevated permissions.

---

## Discovery
- Only Active Capabilities are discoverable by default.
- Deprecated Capabilities remain executable for historical Planning Versions.
- Archived Capabilities are hidden from new Planning.

These invariants ensure that the Capability ecosystem remains secure, extensible, and governed while allowing organizations to continuously expand the platform without affecting existing business workflows.

# Capability Composition

Capabilities are intentionally designed to be small, focused, and composable.

Rather than creating large monolithic Capabilities, complex business processes
should emerge from the composition of smaller Capabilities.

```
Research
↓
Summarize
↓
Write Markdown
↓
Review
↓
Generate PDF
```

Each Capability has one responsibility.

---

# Composition Philosophy

Capability composition follows the Unix philosophy.

Instead of:

```
Generate Promotion Package
```

Prefer:

```
Collect Achievements
↓
Analyze Impact
↓
Write Resume
↓
Review Resume
↓
Generate PDF
↓
Publish
```

Smaller Capabilities maximize:
- reuse
- testing
- observability
- versioning
- provider flexibility

---

# Composition Types

The Runtime supports multiple composition patterns.

```
Sequential
Parallel
Conditional
Pipeline
Loop
Fan-Out
Fan-In
Human Approval
```

These patterns are implemented by Execution Strategies rather than the Capability itself.

---

# Sequential Composition

Capabilities execute in order.

```
Capability A
↓
Capability B
↓
Capability C
```

Each output becomes the input of the next Capability.

---

# Parallel Composition

Independent Capabilities execute simultaneously.

```
           Story
             │
      ┌──────┼──────┐
      │      │      │
Research  Diagram  Metrics
      │      │      │
      └──────┼──────┘
             │
          Merge
```

Parallel execution improves throughput while maintaining deterministic orchestration.

---

# Fan-Out / Fan-In

A Capability may produce multiple independent work items.

Example

```
Generate Documentation
↓
Frontend
Backend
Infrastructure
↓
Merge Documentation
```

Each branch executes independently.

---

# Conditional Composition

Execution path depends on runtime state.

```
Review
↓
Approved?
↓
Yes
↓
Publish
↓
No
↓
Revise
```

Business rules remain explicit and observable.

---

# Loop Composition

Some Capabilities require iterative refinement.

```
Generate
↓
Evaluate
↓
Accepted?
↓
No
↓
Improve
↓
Generate
```

Every loop must define:
- exit condition
- maximum iterations
- timeout

Infinite loops are prohibited.

---

# Long-Running Capabilities

Some Capabilities naturally span hours or days.

Examples

```
Repository Migration
Security Scan
Large Dataset Analysis
Customer Approval
Production Rollout
```

The Runtime treats long-running execution as a normal scenario.

---

# Streaming Outputs

Capabilities may produce incremental results.

Example

```
Generate Book
↓
Chapter 1
↓
Chapter 2
↓
Chapter 3
↓
Completed
```

Streaming outputs improve visibility and enable downstream processing before completion.

---

## Streaming Events

Streaming produces Timeline Events.

```
Output Started
↓
Chunk Produced
↓
Chunk Produced
↓
Output Completed
```

Artifacts may expose partial versions during execution.

---

# Capability Cancellation

Execution may be cancelled.

Cancellation should be cooperative.

```
Running
↓
Cancellation Requested
↓
Cleanup
↓
Cancelled
```

Capabilities should leave the system in a consistent state.

---

# Compensation

Capabilities that modify external systems should define compensation behavior.

Example

```
Deploy
↓
Failure
↓
Rollback
```

Compensation is implemented as separate Capabilities.

It is never hidden inside a Provider.

---

# Capability Testing

Every Capability should include automated tests.

Recommended categories

## Contract Tests

Validate:
- input schema
- output schema
- compatibility

---

## Unit Tests

Validate business behavior.

No Runtime required.

---

## Integration Tests

Validate interaction with:
- Runtime Services
- Artifact Service
- Knowledge Service

Providers should be mocked whenever possible.

---

## End-to-End Tests

Validate complete execution.

```
Planning
↓
Runtime
↓
Capability
↓
Artifact
```

End-to-end tests should remain relatively few.

---

# Capability Certification

Organizations may certify Capabilities before production use.

Example lifecycle

```
Draft
↓
Internal Testing
↓
Certified
↓
Production
↓
Deprecated
```

Certification provides operational confidence.

---

# Operational Metrics

The Runtime collects metrics for every Capability.

Examples

```
Executions
Success Rate
Failure Rate
Average Duration
P95 Duration
Retry Count
Human Requests
Artifacts Produced
Average Cost
Average Token Usage
```

Metrics support governance and optimization.

---

# Capability Health

Capabilities expose operational health.

Example

```
Healthy
↓
Warning
↓
Degraded
↓
Unavailable
```

Health summarizes recent execution quality.

It should not replace detailed diagnostics.

---

# Observability

Capabilities contribute to:
- Timeline
- Metrics
- Logs
- Traces
- Cost reports

Every execution should be fully traceable.

---

# Documentation Requirements

Every production Capability should include:
- Overview
- Business purpose
- Input schema
- Output schema
- Examples
- Constraints
- Supported Strategies
- Supported Providers
- Version history
- Owner

Documentation is part of the Capability contract.

---

# Capability Evolution

Capabilities evolve independently from Runtime.

Possible changes include:
- improved implementation
- additional Providers
- new Strategies
- schema extensions
- performance optimizations

Breaking changes require a new major version.

---

# Recommended Design Guidelines

A Capability should:
- perform one business function
- expose explicit schemas
- remain provider-independent
- produce deterministic outputs where practical
- fail with structured errors
- emit observable events
- remain reusable

A Capability should not:
- orchestrate workflows
- manage retries
- contain business process logic
- reference specific AI models
- call other Providers directly
- persist runtime state

---

# Capability Lifecycle

The complete lifecycle is:

```
Design
↓
Implement
↓
Test
↓
Register
↓
Publish
↓
Discover
↓
Plan
↓
Execute
↓
Observe
↓
Improve
↓
Version
↓
Deprecate
↓
Archive
```

This lifecycle supports continuous evolution without disrupting existing Planning Versions.

---

# Capability Architecture

```
                     Planning
                         │
                         ▼
                  Capability ID
                         │
                         ▼
               Capability Registry
                         │
                         ▼
                Capability Contract
                         │
                         ▼
                Execution Strategy
                         │
                         ▼
                 Provider Selection
                         │
                         ▼
                  Provider Execution
                         │
                         ▼
                     Artifacts
                         │
                         ▼
                Timeline & Metrics
```

Every layer has a single responsibility.

---

# Capability Invariants

The Capability subsystem enforces the following architectural rules.

## Contracts
- Every Capability declares explicit Inputs and Outputs.
- Schemas are validated before execution.
- Published contracts are immutable.

---

## Composition
- Capabilities remain independently executable.
- Composition occurs through Runtime Strategies.
- Long-running Capabilities are first-class citizens.

---

## Observability
- Every execution contributes Timeline Events.
- Every execution publishes Metrics.
- Every execution is traceable.

---

## Evolution
- Capabilities are versioned independently.
- Existing Planning Versions remain reproducible.
- Deprecated Capabilities remain executable until retired.

---

## Independence
- Capabilities never depend on Providers.
- Capabilities never depend on Workflow Engines.
- Capabilities never orchestrate Runtime behavior.
- Infrastructure concerns remain outside the Capability boundary.

---

# Capability Summary

The Capability subsystem is the stable business contract of Leader Control Center.

It bridges Planning and Runtime while remaining independent of providers, workflow engines, and infrastructure.

By separating **what** work should be performed from **how** it is executed and **who** performs it, the platform gains long-term flexibility, portability, and extensibility.

Capabilities become reusable business building blocks that can evolve independently as AI models, execution strategies, and infrastructure continue to change.

