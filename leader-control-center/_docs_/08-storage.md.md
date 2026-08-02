# 08-storage.md

> **Purpose**
>
> This document defines the persistence architecture of Leader Control Center.
>
> Storage is treated as an implementation concern that supports the Domain,
> Runtime, and Capabilities without becoming coupled to any specific database
> technology.
>
> The objective is to ensure that every piece of information has a single owner,
> a clear lifecycle, and an appropriate storage strategy.

---

# Storage Philosophy

Leader Control Center intentionally separates different categories of data.

Different data has different requirements.

Examples:
- transactional consistency
- immutable history
- large binary objects
- search
- semantic retrieval
- analytics
- caching

Attempting to store everything in one database creates unnecessary coupling.

---

# Design Principles

The storage architecture follows these principles.

## Single Source of Truth

Every piece of information has exactly one authoritative owner.

Examples

```
Planning
owns Planning State
Runtime
owns Execution State
Artifact Store
owns Artifact Content
Timeline Store
owns Business Events
```

Copies are projections.

Never sources of truth.

---

## Polyglot Persistence

Different workloads may use different storage technologies.

Examples

```
Relational Database
Object Storage
Search Engine
Vector Database
Cache
Analytics Warehouse
```

Technology choices remain implementation details.

---

## Storage Independence

The Domain depends on repositories.

Repositories depend on storage implementations.

```
Domain
↓
Repository
↓
Storage Adapter
↓
Database
```

Changing databases should not require changing the Domain.

---

# Storage Categories

The platform stores five primary categories of information.

```
Business State
Execution State
Timeline Events
Artifacts
Knowledge
```

Each category has different consistency and scalability requirements.

---

# Business State

Business State represents durable domain entities.

Examples

```
Workspace
Initiative
Epic
Story
Task
Decision
Human Request
```

Characteristics
- transactional
- relational
- strongly consistent
- versioned

---

# Execution State

Execution State belongs to the Runtime.

Examples

```
Execution
Execution Node
Current Status
Retries
Waiting Reason
Progress
Metrics
```

Execution State changes frequently.

Historical execution belongs in Timeline.

---

# Timeline Storage

Timeline stores immutable business events.

Examples

```
Story Started
Capability Completed
Approval Granted
Artifact Published
Execution Failed
```

Timeline is append-only.

Events are never modified.

---

# Artifact Storage

Artifacts represent generated outputs.

Examples

```
Markdown
PDF
Presentation
Spreadsheet
Diagram
Image
JSON
```

Artifacts are immutable after publication.

Artifact metadata is stored separately from artifact content.

---

# Artifact Metadata

Metadata includes

```
Artifact ID
Owner
Type
Version
Created At
Checksum
Content Location
Tags
```

Metadata is optimized for querying.

Binary content is optimized for retrieval.

---

# Knowledge Storage

Knowledge supports planning and execution.

Examples

```
Architecture Documents
Templates
Policies
Reference Material
Examples
Best Practices
```

Knowledge may be indexed for semantic search.

Knowledge should remain independent of Runtime execution.

---

# Search Index

Search is a projection.

It is never the source of truth.

Typical indexed resources

```
Initiatives
Stories
Artifacts
Capabilities
Knowledge
Timeline
```

The index can always be rebuilt from authoritative sources.

---

# Cache

Caching improves performance.

Examples

```
Capability Registry
Configuration
Planning Graph
Permissions
Frequently Accessed Artifacts
```

Cached data is disposable.

The system must continue functioning after cache loss.

---

# Storage Architecture

```
                Domain
                  │
            Repository Layer
                  │
        ┌─────────┼─────────┐
        │         │         │
 Transaction   Event     Artifact
   Store       Store      Store
        │         │         │
        └─────────┼─────────┘
                  │
          Search / Cache
                  │
         Analytics / Vector
```

Each storage type is optimized for its workload.

---

# Repository Pattern

The Domain accesses storage through repositories.

Example

```
StoryRepository
ExecutionRepository
ArtifactRepository
TimelineRepository
KnowledgeRepository
```

Repositories expose business concepts.

They never expose SQL or database APIs.

---

# Repository Responsibilities

Repositories are responsible for:
- persistence
- retrieval
- optimistic locking
- aggregate loading
- transactional boundaries

Repositories are not responsible for:
- business rules
- orchestration
- workflow execution
- provider communication

---

# Transactions

Transactional boundaries align with aggregate boundaries.

Examples

```
Story
Execution
Decision
Human Request
```

Distributed transactions should be avoided whenever possible.

Cross-aggregate consistency is achieved through events.

---

# Optimistic Concurrency

Mutable entities include a version.

```
Entity
↓
Version
↓
Update
↓
Version + 1
```

Conflicting updates fail explicitly.

---

# Immutable Data

The following data should be immutable.

```
Timeline Events
Artifacts
Published Planning Versions
Execution History
Capability Manifests
```

Immutability simplifies auditing and reproducibility.

---

# Storage Invariants

The storage subsystem guarantees the following.

## Ownership
- Every data category has one authoritative owner.
- Projections never become the source of truth.
- Storage ownership aligns with bounded contexts.

---

## Independence
- The Domain depends only on repositories.
- Storage technologies remain replaceable.
- Repository interfaces remain stable.

---

## Durability
- Business State is durable.
- Timeline Events are immutable.
- Artifacts remain versioned and reproducible.

---

## Performance
- Search is projection-based.
- Cache is disposable.
- Analytics never affect transactional correctness.

These invariants establish the storage architecture as a scalable, technology-independent foundation for Leader Control Center.

# Storage Components

The Storage subsystem is composed of specialized stores.

Each store owns a distinct category of information.

```
Storage
├── Transaction Store
├── Event Store
├── Artifact Store
├── Knowledge Store
├── Search Index
├── Vector Store
└── Cache
```

Each component evolves independently.

---

# Transaction Store

The Transaction Store persists mutable business state.

Examples

```
Workspace
Initiative
Epic
Story
Task
Decision
Human Request
Execution
```

Characteristics
- ACID transactions
- optimistic locking
- aggregate consistency
- normalized data model

The Transaction Store is the authoritative source for business entities.

---

# Aggregate Persistence

Each aggregate defines its own transactional boundary.

```
Story
├── Metadata
├── Status
├── Tasks
└── Decisions
```

Repositories load and persist aggregates atomically.

Cross-aggregate transactions should be avoided.

---

# Repository Contracts

Every aggregate exposes a repository.

Example

```
StoryRepository
save()
find()
delete()
exists()
search()
list()
```

Repositories expose business operations rather than database operations.

---

# Repository Responsibilities

Repositories should:
- map aggregates
- enforce optimistic concurrency
- hide persistence details
- support transactions

Repositories should not:
- perform orchestration
- contain business rules
- emit workflow events
- call external systems

---

# Optimistic Locking

Mutable aggregates include a version.

```
Story
Version 12
↓
Update
↓
Version 13
```

Concurrent modifications produce explicit conflicts.

Clients are expected to retry when appropriate.

---

# Event Store

The Event Store persists immutable business events.

Examples

```
Initiative Approved
Story Started
Capability Completed
Human Approved
Artifact Published
```

The Event Store complements transactional state.

It does not replace it.

---

# Event Structure

Every event includes common metadata.

```
Event
id
type
aggregateId
aggregateType
timestamp
actor
correlationId
causationId
payload
```

The payload is immutable after publication.

---

# Event Categories

Events are grouped by intent.

```
Planning Events
Runtime Events
Capability Events
Artifact Events
Human Events
System Events
```

Categories simplify filtering and analytics.

---

# Event Ordering

Ordering is guaranteed within an aggregate.

```
Story
↓
Event 1
↓
Event 2
↓
Event 3
```

Global ordering is not required.

Consumers should rely on aggregate ordering and timestamps.

---

# Event Retention

Business events are retained for auditability.

Retention policies may archive older events.

```
Active
↓
Archive
↓
Cold Storage
```

Archived events remain recoverable.

---

# Timeline Projection

The Timeline is generated from business events.

```
Event Store
↓
Projection
↓
Timeline
```

The Timeline is optimized for user experience.

It is not the authoritative event store.

---

# Projection Model

Projections transform authoritative data into read models.

Examples

```
Timeline
Dashboard
Search
Metrics
Notifications
Reports
```

Projections may be rebuilt at any time.

---

# Projection Pipeline

```
Domain Event
↓
Projection Engine
↓
Projection
↓
Read Model
```

Projection failures should not block transactional commits.

---

# Read Models

Read models optimize common queries.

Examples

```
Execution Summary
Planning Dashboard
Pending Approvals
Capability Usage
Artifact Catalog
```

Read models are disposable.

They can always be regenerated.

---

# Search Index

The Search Index is another projection.

Indexed resources include:

```
Planning
Runtime
Artifacts
Knowledge
Capabilities
```

Search documents denormalize information for fast retrieval.

---

# Indexing Pipeline

```
Entity Updated
↓
Projection
↓
Indexer
↓
Search Document
```

Index updates should be asynchronous.

---

# CQRS Alignment

The architecture naturally aligns with CQRS.

```
Commands
↓
Transaction Store
↓
Domain Events
↓
Projections
↓
Read Models
↓
Queries
```

Commands never read from projections to make business decisions.

---

# Snapshot Strategy

Large aggregates may use snapshots.

```
Aggregate
↓
Snapshot
↓
Incremental Changes
↓
Snapshot
```

Snapshots improve loading performance.

They never replace authoritative state.

---

# Snapshot Guidelines

Recommended snapshot candidates include:

```
Large Planning Graphs
Long-running Executions
Knowledge Collections
```

Snapshot frequency should be configurable.

---

# Data Migration

Storage implementations evolve over time.

Migration principles:
- forward-compatible
- reversible where practical
- observable
- zero business downtime

Migration should preserve aggregate identity.

---

# Backup Strategy

Each storage component defines its own backup policy.

Examples

```
Transaction Store
Continuous Backup
Event Store
Immutable Backup
Artifact Store
Object Replication
Search Index
Rebuild from Source
```

Recovery priorities differ by data category.

---

# Storage Metrics

Operational metrics include:

```
Repository Latency
Transaction Rate
Projection Lag
Indexing Throughput
Snapshot Duration
Storage Size
Conflict Rate
Backup Status
```

Metrics support operational monitoring.

---

# Storage Invariants

The Storage subsystem enforces the following rules.

## Transaction Store
- Aggregates are persisted atomically.
- Optimistic locking prevents lost updates.
- Repository interfaces remain storage-independent.

---

## Event Store
- Events are immutable.
- Aggregate ordering is preserved.
- Event payloads are never modified.

---

## Projections
- Projections are derived data.
- Projections may be rebuilt.
- Projection failures never invalidate committed transactions.

---

## CQRS
- Commands modify authoritative state.
- Queries read optimized projections.
- Business decisions never depend on projection consistency.

These guarantees allow Leader Control Center to scale independently across transactional processing, historical auditing, and high-performance querying while maintaining a clear separation between authoritative state and derived views.

# Artifact Storage

Artifacts are first-class business assets.

Unlike Runtime state, Artifacts are durable deliverables intended for long-term consumption by humans and external systems.

Examples include:

```
Markdown Specification
Architecture Diagram
PowerPoint
PDF
Spreadsheet
Source Code
JSON
Image
Video
Audio
```

Artifacts should remain accessible long after execution has completed.

---

# Artifact Architecture

The Artifact subsystem separates metadata from content.

```
                Artifact
          ┌────────┴────────┐
          │                 │
   Artifact Metadata    Artifact Content
          │                 │
 Transaction Store     Object Storage
```

This enables efficient querying while supporting arbitrarily large artifacts.

---

# Artifact Identity

Every Artifact has a globally unique identity.

```
Artifact
id
workspaceId
type
version
owner
createdAt
createdBy
status
metadata
```

Artifact identifiers remain stable across versions.

---

# Artifact Versioning

Artifacts are immutable.

Updates create new versions.

```
Version 1
↓
Version 2
↓
Version 3
```

Previous versions remain available for:
- audit
- rollback
- comparison
- reproducibility

---

# Version Relationships

```
Artifact
│
├── v1
├── v2
├── v3
└── v4
```

Consumers may request:
- latest
- specific version
- version history

---

# Artifact States

Artifacts progress through a lifecycle.

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

Transitions are governed by Runtime and Human Requests.

---

# Artifact Metadata

Metadata remains transactional.

Example

```
Artifact Metadata
id
version
mimeType
language
owner
labels
tags
checksum
size
storageLocation
retentionPolicy
```

Metadata should remain searchable.

---

# Artifact Content

Content is stored separately.

Supported storage backends include:

```
Local Filesystem
S3 Compatible Storage
Azure Blob
Google Cloud Storage
NAS
Future Providers
```

The Domain depends only on an Artifact Store interface.

---

# Content Addressing

Large artifacts may use content-addressable storage.

```
Content
↓
SHA-256
↓
Content ID
↓
Storage
```

Benefits include:
- deduplication
- integrity verification
- efficient replication

---

# Artifact References

Business entities reference Artifacts.

```
Story
↓
Artifact Reference
↓
Artifact Store
↓
Content
```

Business objects never embed binary content.

---

# Artifact Repository

The Artifact Repository manages metadata.

```
ArtifactRepository
create()
find()
findVersion()
list()
search()
archive()
```

Binary transfer occurs through the Artifact Store.

---

# Artifact Store SPI

The Runtime depends on a storage abstraction.

```
ArtifactStore
put()
get()
delete()
copy()
move()
generateDownloadLink()
generateUploadLink()
```

Implementations may support additional features.

---

# Knowledge Repository

Knowledge is a long-lived organizational asset.

Examples

```
Architecture Guides
Coding Standards
Templates
Policies
Design Documents
Specifications
Meeting Notes
```

Knowledge is distinct from generated Artifacts.

---

# Knowledge Collections

Knowledge is organized into collections.

```
Workspace
↓
Knowledge Collection
↓
Documents
↓
Sections
```

Collections simplify governance and access control.

---

# Knowledge Versioning

Knowledge evolves independently.

```
Document
↓
Revision 1
↓
Revision 2
↓
Revision 3
```

Historical revisions remain available.

---

# Embeddings

Knowledge may be transformed into vector embeddings.

```
Knowledge
↓
Chunking
↓
Embedding
↓
Vector Store
```

Embeddings accelerate semantic retrieval.

Original documents remain authoritative.

---

# Chunking Strategy

Documents are divided into meaningful chunks.

Example

```
Document
↓
Section
↓
Paragraph
↓
Chunk
```

Chunk boundaries should preserve semantic context.

---

# Vector Store

The Vector Store supports similarity search.

Stored information includes:

```
Embedding
Document ID
Chunk ID
Metadata
Embedding Model
Version
```

Vectors are derived data.

They can always be regenerated.

---

# Semantic Search

Semantic search combines multiple sources.

```
User Query
↓
Embedding
↓
Vector Search
↓
Knowledge
↓
Rank
↓
Results
```

Keyword search and semantic search should complement each other.

---

# Hybrid Search

Recommended search pipeline.

```
Keyword Search
+
Vector Search
↓
Merge
↓
Re-rank
↓
Results
```

Hybrid search generally provides better relevance than either approach alone.

---

# Knowledge Governance

Knowledge assets define ownership.

Example

```
Owner
Review Date
Classification
Retention
Tags
Approvers
```

Governance supports trust and discoverability.

---

# Retention Policies

Different storage categories require different retention periods.

Examples

| Category | Suggested Policy |
|----------|------------------|
| Runtime Cache | Hours |
| Search Index | Rebuildable |
| Timeline | Long-term |
| Artifacts | Organization Policy |
| Knowledge | Organization Policy |
| Audit Records | Regulatory Policy |

Retention policies should be configurable.

---

# Data Classification

Stored information may be classified.

Examples

```
Public
Internal
Confidential
Restricted
```

Classification influences:
- encryption
- access control
- sharing
- retention

---

# Encryption

Data should be encrypted.

Recommended practices

```
Encryption At Rest
Encryption In Transit
Managed Keys
Key Rotation
```

Encryption strategy remains implementation-specific.

---

# Workspace Isolation

Storage isolation follows Workspace boundaries.

```
Workspace A
↓
Artifacts
Knowledge
Timeline
Execution
Workspace B
↓
Artifacts
Knowledge
Timeline
Execution
```

Cross-workspace access requires explicit authorization.

---

# Storage Abstraction SPI

Every storage implementation follows a common abstraction.

```
StorageProvider
initialize()
health()
capabilities()
shutdown()
```

Specialized providers extend this interface.

Example

```
ArtifactStore
KnowledgeStore
VectorStore
SearchStore
```

---

# Lifecycle Management

Stored objects follow predictable lifecycle rules.

```
Create
↓
Update Metadata
↓
Publish
↓
Archive
↓
Retention
↓
Delete
```

Deletion should respect retention and compliance policies.

---

# Storage Invariants

The Artifact and Knowledge subsystem guarantees:

## Artifacts
- Artifact content is immutable.
- Metadata is versioned.
- Binary content is stored separately from metadata.
- Artifact references remain stable.

---

## Knowledge
- Original documents remain authoritative.
- Embeddings are derived.
- Vector indexes may be rebuilt.
- Semantic search never replaces source documents.

---

## Security
- Workspace isolation is enforced.
- Classification drives protection policies.
- Encryption is applied independently of storage technology.

---

## Architecture
- Storage implementations remain replaceable.
- Business entities never contain binary payloads.
- Artifact and Knowledge lifecycles remain independent from Runtime execution.

These principles ensure that generated deliverables and organizational knowledge remain durable, searchable, secure, and portable while supporting future storage technologies without affecting the business architecture.

# Storage Technology Mapping

The Storage architecture is intentionally technology-independent.

The platform defines logical storage components rather than prescribing specific technologies.

A typical deployment may map these components as follows.

| Logical Store | Example Technologies |
|---------------|----------------------|
| Transaction Store | PostgreSQL, MySQL, CockroachDB |
| Event Store | PostgreSQL, EventStoreDB |
| Object Store | S3, Azure Blob, Google Cloud Storage, MinIO |
| Search Store | OpenSearch, Elasticsearch |
| Vector Store | pgvector, Milvus, Pinecone, Weaviate |
| Cache | Redis |
| Analytics | ClickHouse, BigQuery, Snowflake |

These mappings are implementation recommendations rather than architectural requirements.

---

# Storage Adapter Pattern

Every storage technology is accessed through an adapter.

```
Repository
↓
Storage SPI
↓
Storage Adapter
↓
Technology
```

Example

```
Artifact Repository
↓
Artifact Store SPI
↓
S3 Adapter
↓
Amazon S3
```

Replacing the adapter should not require changes to the Domain.

---

# Storage Provider SPI

All storage providers implement a common lifecycle.

```
StorageProvider
initialize()
health()
capabilities()
shutdown()
```

Specialized providers extend this contract.

```
TransactionStore
EventStore
ArtifactStore
SearchStore
VectorStore
CacheStore
```

---

# Health Checks

Every storage provider exposes health information.

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

Health information is intended for operational monitoring rather than business logic.

---

# Multi-Region Architecture

The storage architecture should support geographically distributed deployments.

```
Region A
↓
Primary
↓
Replication
↓
Region B
↓
Standby
```

Replication strategy depends on the storage implementation.

---

# High Availability

Storage components should tolerate:
- node failures
- rolling upgrades
- infrastructure maintenance
- transient network failures

Failure of one storage component should be isolated whenever possible.

---

# Backup Strategy

Each logical store defines an independent backup policy.

| Store | Strategy |
|--------|----------|
| Transaction Store | Continuous backup + point-in-time recovery |
| Event Store | Immutable backup |
| Artifact Store | Object replication |
| Knowledge Store | Versioned backup |
| Search Index | Rebuild from authoritative sources |
| Vector Store | Rebuild from Knowledge |
| Cache | No backup required |

Backup policies should align with organizational recovery objectives.

---

# Recovery Objectives

Recommended objectives include:

```
Recovery Point Objective (RPO)
Recovery Time Objective (RTO)
Retention Period
Archive Duration
```

Recovery targets should be defined independently for each storage category.

---

# Disaster Recovery

Recovery follows authoritative ownership.

```
Transaction Store
↓
Business State
↓
Rebuild Projections
↓
Rebuild Search
↓
Rebuild Vector Index
↓
Restore Service
```

Derived storage should be regenerated rather than restored whenever practical.

---

# Projection Rebuild

Every projection must support complete reconstruction.

Examples

```
Timeline
Dashboard
Metrics
Search
Vector Index
```

Rebuild operations should be idempotent.

---

# Data Migration

Storage technologies evolve independently from the Domain.

Migration strategy

```
Old Store
↓
Dual Write (Optional)
↓
Validation
↓
Cutover
↓
New Store
```

Business identifiers remain unchanged throughout migration.

---

# Data Archival

Historical data may be archived.

```
Active
↓
Archive
↓
Cold Storage
↓
Retention Expired
↓
Deletion
```

Archived information should remain discoverable through metadata.

---

# Data Deletion

Deletion policies vary by data type.

Examples

```
Cache
Immediate
Search Index
Rebuild
Artifacts
Retention Policy
Business Records
Organization Policy
```

Deletion should be observable and auditable.

---

# Data Integrity

Storage providers should support integrity verification.

Examples

```
Checksums
Content Hashes
Version Numbers
Optimistic Locking
```

Integrity validation should occur independently of application logic.

---

# Storage Security

Recommended security controls include:

```
Encryption At Rest
Encryption In Transit
Key Rotation
Access Logging
Least Privilege
Immutable Audit Logs
```

Security mechanisms remain infrastructure concerns.

---

# Compliance

Organizations may apply compliance policies.

Examples

```
Retention Rules
Legal Hold
Data Residency
Export Restrictions
PII Handling
```

The storage architecture should accommodate these requirements without changing the Domain Model.

---

# Observability

Every storage component contributes operational telemetry.

Examples

```
Read Latency
Write Latency
Transaction Duration
Projection Lag
Storage Capacity
Replication Delay
Backup Status
Restore Duration
Cache Hit Rate
Indexing Throughput
```

Operational metrics remain separate from business metrics.

---

# Capacity Planning

Storage growth should be monitored independently.

Categories include:

```
Business State
Execution State
Artifacts
Knowledge
Timeline
Search Index
Vectors
```

Each category may scale at different rates.

---

# Reference Architecture

```
                   Domain
                      │
               Repository Layer
                      │
      ┌───────────────┼────────────────┐
      │               │                │
 Transaction      Event Store     Artifact Store
     Store             │                │
      │                │          Object Storage
      │                │                │
      ├────────────┬───┴───────┬────────┤
      │            │           │        │
 Search Index   Timeline   Knowledge  Vector Store
      │                        │
      └──────────────┬─────────┘
                     │
                  Cache
```

Every component communicates through well-defined interfaces.

---

# Storage Design Guidelines

Storage implementations should:
- remain replaceable
- expose health information
- support versioning
- isolate infrastructure concerns
- publish operational metrics
- preserve data ownership boundaries

Storage implementations should not:
- contain business logic
- expose database APIs to the Domain
- become the source of truth for derived data
- tightly couple repositories to technologies

---

# Storage Invariants

The Storage subsystem guarantees the following.

## Ownership
- Every logical data category has one authoritative owner.
- Derived data is always rebuildable.
- Repository interfaces remain stable.

---

## Durability
- Business state is durable.
- Timeline events are immutable.
- Artifact content is versioned.
- Knowledge remains independently versioned.

---

## Portability
- Storage technologies are replaceable.
- Adapters isolate implementation details.
- Domain code remains storage-agnostic.

---

## Recovery
- Backups protect authoritative data.
- Projections are regenerated.
- Cache is disposable.
- Recovery preserves business identity.

---

## Scalability
- Storage components scale independently.
- Search, vectors, analytics, and cache evolve independently of transactional storage.
- Object storage is optimized for large artifacts.

---

# Storage Summary

The Storage subsystem provides the durable foundation of Leader Control Center.

By separating transactional state, immutable events, artifacts, knowledge, search, vectors, and cache into independently managed logical stores, the platform achieves scalability, portability, and operational resilience.

The architecture intentionally treats storage technologies as interchangeable infrastructure while preserving stable repository contracts for the Domain. This allows the platform to adopt new databases, object stores, search engines, and vector technologies over time without impacting business logic, APIs, or workflow execution.
