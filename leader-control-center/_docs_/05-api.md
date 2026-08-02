# 05-api.md

> **Purpose**
>
> This document defines the public API of Leader Control Center.
>
> The API exposes business capabilities to users, applications, and external systems.
>
> It intentionally hides:
>
> - Workflow engines
> - Providers
> - AI models
> - Runtime implementation
> - Internal orchestration
>
> The API is a stable business contract.

---

# API Philosophy

The API should expose business operations.

It should never expose infrastructure.

Good examples

```
Create Initiative
Start Story
Approve Request
Generate Artifact
Search Capabilities
```

Poor examples

```
Signal Workflow
Execute Activity
Call GPT
Resume Temporal
Invoke MCP
```

Business APIs survive implementation changes.

---

# API Design Principles

The API follows several core principles.

## Business-Oriented

Resources model business concepts.

```
Workspace
Initiative
Story
Task
Execution
Artifact
Capability
Human Request
```

Infrastructure objects remain internal.

---

## Command-Query Separation

Commands modify state.

Queries return information.

Commands

```
Start Story
Approve Request
Publish Artifact
```

Queries

```
Get Story
List Artifacts
Search Capabilities
Get Timeline
```

Commands never return complex projections.

Queries never modify state.

---

## API First

Every platform capability must be accessible through the API.

The UI is implemented entirely using the public API.

There are no privileged frontend endpoints.

---

## Engine Independence

The API must never expose:
- Temporal Workflow IDs
- Activity IDs
- Signal names
- Provider identifiers
- Prompt identifiers

Clients interact only with business objects.

---

# API Architecture

```
                Frontend
                    │
             REST / WebSocket
                    │
               API Gateway
                    │
              Business API
                    │
          Application Services
                    │
            Domain Model
                    │
          Runtime / Planning
                    │
        Workflow Adapter Layer
```

Every layer has a single responsibility.

---

# Resource Model

The API exposes the following top-level resources.

```
Workspace
Initiative
Epic
Story
Task
Execution
Capability
Artifact
Human Request
Decision
```

Each resource has its own endpoint family.

---

# Endpoint Structure

Resources follow predictable paths.

```
/workspaces
/initiatives
/stories
/tasks
/executions
/capabilities
/artifacts
/requests
/decisions
```

Sub-resources remain hierarchical.

Example

```
/initiatives/{id}/stories
/stories/{id}/tasks
/executions/{id}/timeline
/executions/{id}/artifacts
```

---

# API Style

The API is resource-oriented.

Business actions are expressed using commands.

Example

```
POST /stories/{id}/start
POST /stories/{id}/cancel
POST /requests/{id}/approve
POST /artifacts/{id}/publish
```

Avoid generic update endpoints when a business command exists.

---

# API Versioning

The API is versioned independently of:
- Capabilities
- Providers
- Runtime
- Planning

Example

```
/api/v1
/api/v2
```

Breaking changes require a new major version.

---

# Content Types

Primary formats

```
application/json
```

Future support

```
application/problem+json
text/event-stream
application/octet-stream
```

Artifacts may expose additional content types depending on their format.

---

# Resource Identifiers

All business resources use opaque identifiers.

Example

```
initiative_01HV...
story_01HV...
execution_01HV...
artifact_01HV...
```

Clients must never infer meaning from identifiers.

---

# Pagination

Collection endpoints support cursor-based pagination.

Example

```
GET /artifacts?cursor=...
GET /executions?cursor=...
```

Cursor pagination provides stable traversal for large datasets.

---

# Filtering

Collection endpoints support filtering.

Examples

```
status=Running
owner=alice
priority=High
category=Research
capability=GenerateMarkdown
```

Filtering semantics remain consistent across resources.

---

# Sorting

Supported sort fields include:

```
createdAt
updatedAt
priority
status
startedAt
completedAt
name
```

Sorting order

```
asc
desc
```

---

# Expansion

Related resources may be expanded.

Example

```
GET /stories/{id}
?expand=tasks
?expand=executions
?expand=artifacts
```

Expansion reduces unnecessary network requests while keeping the API predictable.

---

# API Invariants

The API enforces the following rules.

1. Business resources are stable.
2. Infrastructure details are hidden.
3. Commands express business intent.
4. Queries never mutate state.
5. Resource identifiers are opaque.
6. Versioning is explicit.
7. The frontend consumes only public APIs.
8. The API remains independent of providers and workflow engines.

These invariants establish the API as the stable external contract of Leader Control Center.

# Resource Endpoints

Each business resource exposes a consistent set of operations.

The API follows predictable patterns across every resource.

```
Create
Get
List
Search
Archive
Restore
```

Business actions are modeled as Commands.

---

# Workspace API

## Commands

```
POST /workspaces
```

Create a new Workspace.

```
POST /workspaces/{id}/archive
```

Archive a Workspace.

---

## Queries

```
GET /workspaces/{id}
GET /workspaces
GET /workspaces/{id}/statistics
```

---

# Initiative API

Initiatives represent the highest level of planning.

---

## Commands

```
POST /initiatives
POST /initiatives/{id}/approve
POST /initiatives/{id}/freeze
POST /initiatives/{id}/start
POST /initiatives/{id}/cancel
POST /initiatives/{id}/clone
```

---

## Queries

```
GET /initiatives/{id}
GET /initiatives
GET /initiatives/{id}/planning
GET /initiatives/{id}/executions
GET /initiatives/{id}/metrics
```

---

# Story API

---

## Commands

```
POST /stories
POST /stories/{id}/approve
POST /stories/{id}/start
POST /stories/{id}/pause
POST /stories/{id}/resume
POST /stories/{id}/cancel
POST /stories/{id}/archive
```

---

## Queries

```
GET /stories/{id}
GET /stories
GET /stories/{id}/tasks
GET /stories/{id}/timeline
GET /stories/{id}/artifacts
```

---

# Task API

---

## Commands

```
POST /tasks
POST /tasks/{id}/move
POST /tasks/{id}/split
POST /tasks/{id}/merge
POST /tasks/{id}/archive
```

---

## Queries

```
GET /tasks/{id}
GET /tasks
GET /tasks/{id}/dependencies
```

Tasks are planning resources.

Runtime execution is exposed separately.

---

# Execution API

Execution APIs expose runtime state.

---

## Commands

```
POST /executions/{id}/pause
POST /executions/{id}/resume
POST /executions/{id}/cancel
POST /executions/{id}/retry
```

Execution commands express business intent.

They do not expose workflow operations.

---

## Queries

```
GET /executions
GET /executions/{id}
GET /executions/{id}/timeline
GET /executions/{id}/metrics
GET /executions/{id}/artifacts
GET /executions/{id}/health
```

---

# Capability API

The Capability Registry is exposed through dedicated endpoints.

---

## Queries

```
GET /capabilities
GET /capabilities/{id}
GET /capabilities/categories
GET /capabilities/search
GET /capabilities/{id}/versions
GET /capabilities/{id}/documentation
```

Capabilities are immutable.

No public update endpoint exists.

---

# Artifact API

Artifacts are immutable execution outputs.

---

## Commands

```
POST /artifacts/{id}/approve
POST /artifacts/{id}/publish
POST /artifacts/{id}/archive
```

---

## Queries

```
GET /artifacts
GET /artifacts/{id}
GET /artifacts/{id}/content
GET /artifacts/{id}/versions
GET /artifacts/{id}/history
```

---

# Human Request API

Human Requests represent work requiring user attention.

---

## Commands

```
POST /requests/{id}/approve
POST /requests/{id}/reject
POST /requests/{id}/clarify
POST /requests/{id}/delegate
POST /requests/{id}/answer
POST /requests/{id}/select-option
```

---

## Queries

```
GET /requests
GET /requests/{id}
GET /requests/attention
GET /requests/assigned
GET /requests/history
```

---

# Decision API

Decisions are immutable.

---

## Queries

```
GET /decisions
GET /decisions/{id}
GET /requests/{id}/decision
```

Decisions are never updated.

---

# Timeline API

Timeline is append-only.

```
GET /timeline
GET /timeline/{executionId}
GET /timeline/{executionId}/events
```

Timeline queries support filtering.

```
category
source
type
since
until
```

---

# Metrics API

Metrics are optimized for dashboards.

```
GET /metrics
GET /metrics/runtime
GET /metrics/providers
GET /metrics/cost
GET /metrics/workspaces
```

Metrics are read-only projections.

---

# Search API

Global search spans all business resources.

```
GET /search
```

Supported targets

```
Initiatives
Stories
Tasks
Artifacts
Capabilities
Executions
Human Requests
```

Example

```
GET /search?q=promotion
```

---

# Bulk Operations

Bulk operations are explicit commands.

```
POST /stories/archive
POST /tasks/move
POST /artifacts/publish
```

Request

```
{
    "ids": [
        "...",
        "...",
        "..."
    ]
}
```

Bulk operations should report partial success.

---

# Long-Running Operations

Some commands complete asynchronously.

Example

```
POST /initiatives/{id}/start
```

Response

```
202 Accepted
Location:
/operations/op_123
```

The client may poll the operation or subscribe to execution updates.

---

# Operation Resource

```
GET /operations/{id}
```

Example

```
Operation
id
status
progress
resource
createdAt
completedAt
```

Operation resources are transient.

Business state lives in Runtime.

---

# Optimistic Concurrency

Mutable planning resources expose a version.

Example

```
If-Match: 14
```

Conflicting updates return

```
409 Conflict
```

This prevents accidental overwrites.

---

# Idempotency

Every command endpoint supports an Idempotency-Key.

Example

```
POST /initiatives
Idempotency-Key:
2db4...
```

Duplicate requests return the original result.

This is required for reliable retries.

---

# Error Model

Errors follow RFC 9457 (`application/problem+json`).

Example

```
{
  "type": "...",
  "title": "...",
  "status": 409,
  "detail": "...",
  "instance": "...",
  "traceId": "..."
}
```

Business errors should remain understandable by non-technical clients.

---

# Common Status Codes

```
200 OK
201 Created
202 Accepted
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Failed
429 Too Many Requests
500 Internal Error
```

---

# API Invariants

The API layer guarantees:
- All commands are idempotent.
- All long-running work returns `202 Accepted`.
- Every mutable planning resource supports optimistic concurrency.
- Timeline and Metrics are read-only.
- Decisions and Artifacts are immutable after creation.
- Errors use a consistent Problem Details format.
- Public APIs never expose provider or workflow-engine implementation details.

These guarantees provide a predictable and durable contract for all clients while allowing the platform implementation to evolve independently.

# Authentication

Leader Control Center is an API-first platform.

Every API request is authenticated before reaching the Domain Layer.

Authentication is intentionally separated from authorization.

```
Client
↓
Authentication
↓
Authorization
↓
Business API
↓
Domain
```

The Domain should never know how authentication was performed.

---

# Identity Model

Every authenticated request resolves to an Identity.

```
Identity
id
type
workspace
roles
permissions
metadata
```

Identity types include:

```
Human User
Service Account
Automation
API Client
```

The Runtime uses Identity for auditing only.

---

# Authentication Providers

Authentication is pluggable.

Supported examples

```
OIDC
OAuth2
SAML
LDAP
Internal Identity
API Keys
mTLS
```

Authentication providers should be replaceable without changing the API.

---

# Authorization

Authorization evaluates whether an Identity may perform a business action.

```
Identity
↓
Policy Engine
↓
Allow
or
Deny
```

Authorization occurs before command execution.

---

# Authorization Model

Leader Control Center uses policy-based authorization.

Policies evaluate:

```
Workspace
Role
Permission
Resource
Business Rules
```

Policies remain external to business logic.

---

# Workspace Isolation

Workspaces are strict security boundaries.

```
Workspace A
≠
Workspace B
```

Resources never cross workspace boundaries unless explicitly shared.

Every resource belongs to exactly one Workspace.

---

# Multi-Tenancy

The platform is multi-tenant by design.

```
Organization
↓
Workspace
↓
Initiatives
↓
Executions
```

All API operations are scoped to a Workspace.

Cross-workspace queries require explicit authorization.

---

# Role Model

Suggested built-in roles

```
Workspace Owner
Administrator
Leader
Contributor
Reviewer
Observer
Automation
```

Organizations may define custom roles.

---

# Permission Model

Permissions are business-oriented.

Examples

```
Create Initiative
Approve Planning
Execute Stories
Publish Artifacts
Review Documents
Manage Capabilities
Manage Plugins
```

Avoid infrastructure permissions such as:

```
Signal Workflow
Execute Activity
Invoke Provider
```

---

# API Tokens

Service-to-service integrations may use API Tokens.

Example

```
Token
id
workspace
expiresAt
permissions
createdBy
```

Tokens inherit the permissions granted to them.

---

# Event Streaming

The platform publishes real-time updates.

Clients should not poll continuously.

```
Runtime
↓
Events
↓
Streaming API
↓
Clients
```

---

# Server-Sent Events

Server-Sent Events (SSE) provide lightweight streaming.

Example

```
GET /events
```

Possible events

```
Execution Updated
Artifact Generated
Human Request Created
Timeline Event
Metrics Updated
```

SSE is recommended for dashboards.

---

# WebSocket API

Interactive applications may use WebSockets.

Example

```
/ws
```

Typical messages

```
Execution Progress
Timeline Updates
Attention Queue
Notifications
```

The protocol remains event-based.

---

# Subscription Model

Clients explicitly subscribe to resources.

Examples

```
Execution
Initiative
Workspace
Timeline
Attention Queue
```

Subscriptions reduce unnecessary traffic.

---

# Event Envelope

All streamed events share a common envelope.

```
Event
id
timestamp
workspaceId
resourceType
resourceId
eventType
payload
```

Clients process events consistently regardless of source.

---

# API Extensibility

Plugins may extend the API.

Extensions are additive.

```
Core API
+
Plugin Endpoints
↓
Unified API
```

Plugins may not override existing endpoints.

---

# Extension Guidelines

Plugins may expose:

```
Custom Queries
Custom Commands
Custom Resources
```

Extensions must:
- declare schemas
- declare permissions
- declare documentation
- follow versioning rules

---

# OpenAPI

Every endpoint must be described using OpenAPI.

The specification is the canonical contract.

Generated artifacts include:

```
OpenAPI
JSON Schema
SDKs
Documentation
```

Implementation should conform to the specification.

---

# SDK Generation

Official SDKs are generated automatically.

Target languages

```
TypeScript
Java
Kotlin
Python
Go
C#
```

Generated SDKs should expose business terminology.

---

# API Deprecation

Deprecated endpoints remain supported for a defined period.

Lifecycle

```
Active
↓
Deprecated
↓
Sunset
↓
Removed
```

Deprecation notices should include migration guidance.

---

# Rate Limiting

Rate limiting protects platform stability.

Limits may be defined by:

```
Workspace
Identity
API Token
Endpoint
Organization
```

Rate limiting is transparent to the Domain Layer.

---

# Correlation IDs

Every request receives a Correlation ID.

Example

```
X-Correlation-Id
```

The identifier propagates through:
- API
- Runtime
- Providers
- Timeline
- Logs

This enables end-to-end tracing.

---

# API Observability

Every API request contributes telemetry.

Collected data includes:

```
Latency
Request Count
Error Rate
Authentication Failures
Authorization Failures
Payload Size
Streaming Connections
```

These metrics support operational monitoring.

---

# GraphQL Considerations

REST is the primary API.

GraphQL may be provided as a projection layer.

```
GraphQL
↓
REST Commands
↓
Domain
```

GraphQL should never bypass business commands or authorization.

---

# API Invariants

The API subsystem enforces the following rules.

## Security
- Every request is authenticated.
- Every command is authorized.
- Workspaces are isolated security boundaries.
- Authorization uses business permissions.

---

## Streaming
- Events are immutable.
- Clients subscribe explicitly.
- Event ordering is preserved per resource.

---

## Extensibility
- Plugins may extend but never replace the Core API.
- Extensions must publish OpenAPI schemas.
- Extensions follow the same authentication and authorization model.

---

## Contracts
- OpenAPI is the canonical API specification.
- SDKs are generated from OpenAPI.
- Deprecated endpoints remain functional until their published sunset date.

These invariants ensure that the API remains secure, extensible, observable, and stable for both first-party and third-party clients.

# Command Processing Pipeline

Every business command follows the same processing lifecycle.

This guarantees consistency across the platform.

```
HTTP Request
↓
Authentication
↓
Authorization
↓
Validation
↓
Application Service
↓
Domain
↓
Events
↓
Persistence
↓
Read Models
↓
Response
```

Each stage has a single responsibility.

---

# Request Lifecycle

## 1. Receive Request

The API validates:
- Content-Type
- Authentication
- API Version
- Request Format

Malformed requests are rejected immediately.

---

## 2. Authorization

Business permissions are evaluated.

Examples

```
Approve Story
Publish Artifact
Manage Capabilities
```

Authorization completes before business validation.

---

## 3. Validation

Validation occurs in two phases.

### Structural
- JSON schema
- Required fields
- Types
- Formats

### Business
- Domain invariants
- Workspace rules
- Planning state
- Runtime state

Only valid commands reach the Domain.

---

## 4. Domain Execution

Application Services translate requests into business commands.

```
API
↓
Application Service
↓
Command
↓
Domain
```

The Domain never receives HTTP objects.

---

## 5. Event Publication

Successful commands emit immutable Domain Events.

```
Command
↓
Domain Event
↓
Timeline
↓
Read Models
↓
Subscribers
```

Events are the primary integration mechanism.

---

## 6. Response

Responses depend on command type.

Immediate

```
200 OK
201 Created
```

Asynchronous

```
202 Accepted
```

Errors

```
4xx
5xx
```

---

# Asynchronous Operations

Long-running commands return immediately.

Example

```
POST
/initiatives/{id}/start
```

Response

```
202 Accepted
Operation ID
Execution ID
```

Progress is observed through Runtime resources.

---

# Polling

Clients may poll operation status.

```
GET
/operations/{id}
```

Possible states

```
Pending
Running
Completed
Failed
Cancelled
```

Polling is optional.

Streaming is preferred.

---

# Event Streaming

The preferred mechanism for progress updates.

```
Runtime
↓
Timeline Events
↓
Streaming API
↓
Client
```

Clients receive incremental updates.

No repeated polling required.

---

# Webhooks

External systems may subscribe using Webhooks.

```
Runtime
↓
Webhook Dispatcher
↓
External System
```

Supported events

```
Execution Completed
Artifact Published
Approval Requested
Execution Failed
Capability Registered
```

---

# Webhook Registration

Example

```
POST
/webhooks
```

Configuration

```
Endpoint
Secret
Events
Retry Policy
Workspace
```

Webhooks are scoped to one Workspace.

---

# Webhook Delivery

Delivery guarantees

```
At Least Once
```

Consumers must treat deliveries as idempotent.

Every event includes:

```
Event ID
Timestamp
Signature
Correlation ID
```

---

# Batch APIs

Some operations support batching.

Example

```
POST
/tasks/archive
```

Request

```
ids[]
reason
```

Response

```
Succeeded
Failed
Skipped
```

Batch execution should isolate failures.

---

# Import API

Planning may be imported.

Supported formats

```
Markdown
JSON
YAML
CSV
OpenAPI
Git Repository
```

Import creates Planning resources only.

Runtime is unaffected.

---

# Export API

Resources may be exported.

Supported formats

```
Markdown
JSON
YAML
PDF
HTML
```

Example

```
Planning Graph
↓
Markdown
```

Exports are immutable snapshots.

---

# API Governance

The API evolves under governance.

Changes are categorized.

```
Patch
Minor
Major
```

Breaking changes require a major version.

---

# API Review Process

Every new endpoint should answer:

```
Is this a business resource?
Is this a business command?
Can an existing endpoint be reused?
Does this expose infrastructure?
Does this leak Runtime implementation?
```

Endpoints failing these questions should be redesigned.

---

# Naming Guidelines

Resource names

```
Plural
/workspaces
/stories
/artifacts
```

Commands

```
Verb
/start
/approve
/publish
/archive
```

Queries remain resource-oriented.

---

# Response Design

Responses should expose business information.

Good

```
Story Status
Execution Progress
Planning Health
```

Poor

```
Workflow Thread
Activity Queue
Signal Count
```

Infrastructure terminology remains hidden.

---

# Error Design

Errors should be actionable.

Example

Instead of

```
Workflow Signal Failed
```

Prefer

```
Story cannot resume because approval is still pending.
```

Errors communicate business meaning.

---

# API Architecture

```
                    Client Applications
                             │
             ┌───────────────┼────────────────┐
             │               │                │
          Web UI          Mobile UI       Third Parties
             │               │                │
             └───────────────┼────────────────┘
                             │
                        API Gateway
                             │
               Authentication / Authorization
                             │
                     Business API Layer
                             │
                  Application Services Layer
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
     Planning             Runtime          Capability Registry
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                     Workflow Adapter
                             │
                     Provider Layer
                             │
                  Infrastructure Services
```

Each layer communicates only with its immediate neighbor.

---

# API Design Principles

The Leader Control Center API follows these principles.

## Stable

Business resources evolve slowly.

Infrastructure evolves independently.

---

## Explicit

Commands communicate intent.

Hidden side effects are avoided.

---

## Observable

Every command generates:
- Timeline Events
- Metrics
- Correlation IDs
- Audit records

---

## Consistent

Resources follow the same conventions.

Clients should learn one pattern.

---

## Extensible

New Capabilities

New Providers

New Plugins

New Runtime features

should require little or no API redesign.

---

## Technology Independent

The API must not expose:
- Temporal
- Kafka
- PostgreSQL
- OpenAI
- Anthropic
- MCP
- Kubernetes

These are implementation details.

---

# API Invariants

The API layer guarantees the following.

## Commands
- Every command expresses business intent.
- Commands are idempotent.
- Long-running commands return immediately.

---

## Queries
- Queries never modify state.
- Read models are optimized independently of writes.
- Timeline and Metrics remain append-only projections.

---

## Contracts
- OpenAPI is the canonical contract.
- SDKs are generated from the specification.
- API versions remain backward compatible within a major release.

---

## Security
- Every request is authenticated.
- Every request is authorized.
- Every request is traceable.

---

## Architecture
- Business concepts are exposed.
- Infrastructure concepts remain hidden.
- The API remains independent of Providers and Workflow Engines.

---

# API Summary

The API is the public contract of Leader Control Center.

It exposes Planning, Runtime, Capabilities, Artifacts, and Human Collaboration through a consistent business-oriented interface while shielding clients from workflow engines, providers, and infrastructure.

By treating the API as a long-lived business contract rather than an implementation layer, the platform can continuously evolve internally while preserving compatibility for users, SDKs, plugins, and external integrations.
