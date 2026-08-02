# 02-planning.md

> **Purpose**
>
> This document specifies the Planning Domain.
>
> Planning is responsible for transforming a business objective into an executable plan.
>
> Planning intentionally contains **no runtime state**.
>
> It should remain stable regardless of retries, execution failures, provider changes or workflow engine implementations.

---

# Planning Philosophy

Planning represents **intent**.

Execution represents **reality**.

The planning layer should answer one question:

> "What needs to be accomplished?"

It should never answer:
- Which provider executes this?
- Which workflow engine runs this?
- Which AI model should be selected?
- How many retries occurred?

Those belong exclusively to runtime.

---

# Planning Principles

## Business Driven

Planning should always model business outcomes before technical implementation.

Good planning:

```
Write Promotion Document
↓
Review
↓
Submit
```

Poor planning:

```
GPT
↓
Claude
↓
Temporal Activity
```

Planning should remain understandable by leaders.

---

## Stable

Planning should change slowly.

Execution should change frequently.

The same plan may execute dozens of times.

```
Planning
↓
Execution #1
↓
Execution #2
↓
Execution #3
```

---

## Explicit Before Autonomous

Every autonomous capability must first exist as an explicit planning capability.

Users should always be able to:
- manually define work
- ask AI for suggestions
- delegate planning

without changing the planning model.

---

# Planning Hierarchy

The complete hierarchy is:

```
Workspace
↓
Initiative
↓
Epic
↓
Story
↓
Task
```

Each level has a distinct responsibility.

---

# Workspace

Planning begins inside a Workspace.

The Workspace defines:
- planning templates
- capability catalog
- AI defaults
- planning policies
- provider availability

The Workspace itself contains no business work.

---

# Initiative

The Initiative represents a business objective.

Examples:
- Promotion to P3
- Platform Modernization
- Search V2
- AI Adoption
- Database Migration

Every planning artifact belongs to exactly one Initiative.

---

## Initiative Structure

```
Initiative
├── Vision
├── Objectives
├── Success Metrics
├── Epics
├── Planning Metadata
└── Runtime References
```

---

## Initiative Properties

```
id
name
description
owner
status
priority
startDate
targetDate
labels
metadata
```

---

## Initiative Responsibilities

An Initiative is responsible for:
- grouping related work
- tracking business outcomes
- organizing priorities
- exposing progress
- providing context

An Initiative is **not** responsible for execution.

---

# Epic

An Epic is the primary planning container.

It groups Stories that contribute toward a common objective.

Example:

```
Promotion to P3
↓
Epic
Promotion Package
↓
Stories
```

---

## Epic Responsibilities
- organize Stories
- define milestones
- prioritize delivery
- group related work

Epics exist primarily for planning.

Leaders rarely interact with Epics directly.

---

## Epic Structure

```
Epic
id
initiativeId
title
description
priority
status
targetDate
metadata
```

---

# Story

Stories represent meaningful business deliverables.

Examples:
- Architecture Proposal
- Technical Design
- Resume
- Presentation
- Migration Plan

Stories should always produce measurable business value.

---

## Story Responsibilities

Stories own:
- Tasks
- Acceptance Criteria
- Dependencies
- Estimates
- Priority

Stories never own runtime state.

---

## Story Structure

```
Story
id
epicId
title
description
planningMode
priority
estimate
status
```

---

# Story Lifecycle

```
Draft
↓
Backlog
↓
Ready
↓
In Progress
↓
Completed
↓
Archived
```

This lifecycle describes planning progress.

It does not describe runtime execution.

---

# Story Acceptance Criteria

Every Story should define clear acceptance criteria.

Example:

```
Architecture Proposal
Acceptance Criteria
✓ Covers current architecture
✓ Covers proposed architecture
✓ Includes migration plan
✓ Reviewed by Tech Lead
```

Acceptance Criteria become runtime completion checks.

---

# Story Dependencies

Stories may depend on other Stories.

```
Story A
↓
Story B
↓
Story C
```

Dependencies define planning order.

Execution engines may choose different scheduling strategies later.

Planning remains independent.

---

# Task

Tasks are the smallest planning unit.

Tasks represent **work to be accomplished**.

Tasks intentionally avoid implementation details.

Good examples:
- Research competitors
- Write README
- Generate diagram
- Review proposal
- Collect metrics

Poor examples:
- Call GPT
- Execute Activity
- Invoke Claude

Tasks describe intent.

Not execution.

---

# Task Responsibilities

Tasks define:
- objective
- planning mode
- dependencies
- acceptance criteria
- execution constraints

Tasks never define:
- provider
- workflow engine
- retry policy
- AI model
- execution strategy

Those decisions belong to runtime.

---

# Task Structure

```
Task
id
storyId
title
description
planningMode
priority
estimate
constraints
acceptanceCriteria
metadata
```

---

# Task Lifecycle

```
Draft
↓
Ready
↓
Cancelled
```

Notice there is **no Completed state**.

Completion belongs to **Task Execution**, not the Task itself.

Planning remains immutable.

Execution records completion.

# Planning Modes

Leader Control Center supports multiple planning modes while maintaining a single execution model.

The goal is to progressively increase autonomy without changing the underlying architecture.

```
Planning Mode
├── Structured
├── Goal-Oriented
├── Template (Future)
├── Imported (Future)
└── AI Generated (Future)
```

Regardless of the planning mode, every Task is normalized into the same execution graph before runtime.

---

# Structured Planning

Structured Planning is the default mode.

The planner explicitly defines:
- Task
- Capability
- Dependencies
- Constraints
- Acceptance Criteria

Example

```
Story
Create Architecture Document
Tasks
Research Existing System
↓
Write Markdown
↓
Generate Diagram
↓
Review
↓
Publish
```

This planning mode is deterministic and predictable.

It is the recommended mode for production environments.

---

## Structured Task

A Structured Task explicitly declares the Capability required to complete the work.

```
Task
Generate Architecture Diagram
Capability
Generate Diagram
```

Execution does not need to infer intent.

---

# Goal-Oriented Planning

Goal-Oriented Planning allows the planner to describe **the desired outcome** rather than the implementation.

Example

```
Goal
Prepare an executive architecture proposal
ready for review.
Constraints
- Maximum 10 pages
- Mermaid diagrams
- Markdown source
Success Criteria
- Executive quality
- Complete
- Technically accurate
```

The AI Planner expands the goal into executable Tasks.

---

## Goal Planning Pipeline

```
Goal
↓
AI Planner
↓
Stories
↓
Tasks
↓
Capabilities
↓
Execution
```

Once planning is complete, the runtime behaves identically to Structured Planning.

---

# Progressive Planning

Users should naturally evolve through increasing levels of automation.

```
Manual Planning
↓
AI Suggestions
↓
Goal-Oriented Planning
↓
Autonomous Planning
```

The transition between stages should never require migrating existing Initiatives.

---

# Planning Constraints

Constraints provide additional guidance to planning.

Examples

```
Must use Mermaid
Maximum 5 pages
Use company template
Generate Markdown only
Human review required
No external internet
Use internal documentation
```

Constraints influence planning but do not directly control execution.

---

## Constraint Categories

Suggested categories

```
Technical
Business
Security
Compliance
Formatting
Performance
Budget
Provider
Human Governance
```

Constraints remain business concepts.

---

# Planning Templates

Templates allow organizations to standardize planning.

Examples

```
Architecture Proposal
Promotion Package
Incident Review
Migration Plan
RFC
Product Specification
Quarterly Planning
```

Templates create initial planning structures.

Users remain free to customize them.

---

## Template Structure

```
Template
id
name
description
defaultStories
defaultTasks
recommendedCapabilities
metadata
```

Templates never contain runtime information.

---

# Story Composition

Stories are composed of ordered Tasks.

```
Story
↓
Task
↓
Task
↓
Task
```

Ordering defines planning intent.

Execution strategies may optimize scheduling later.

---

# Task Dependencies

Tasks may depend on one or more Tasks.

```
Task A
↓
Task B
↓
Task C
```

or

```
Task A
Task B
↓
Task C
```

Dependencies are directed and acyclic.

Circular dependencies are invalid.

---

## Dependency Rules

A Task may:
- depend on zero or more Tasks
- be depended on by zero or more Tasks

A dependency always exists within the same Story.

Cross-Story dependencies should occur through Story Dependencies.

---

# Story Dependencies

Stories may also depend on other Stories.

Example

```
Architecture
↓
Implementation Plan
↓
Migration Plan
```

Story Dependencies provide high-level sequencing.

Task Dependencies remain local to a Story.

---

# Acceptance Criteria

Acceptance Criteria define when planning work is considered complete.

They are business rules.

Examples

```
✓ Reviewed by manager
✓ PDF generated
✓ Markdown committed
✓ Architecture diagram included
✓ References added
```

Acceptance Criteria should be objective whenever possible.

---

## Acceptance Criterion Structure

```
Acceptance Criterion
id
description
required
verificationMethod
metadata
```

Verification may be:
- Human
- AI
- Rule
- External System

---

# Estimation

Planning supports lightweight estimation.

Examples

```
Small
Medium
Large
```

or

```
30 min
2 hours
1 day
3 days
```

Estimations are advisory.

Runtime measurements always represent actual execution.

---

# Labels

Labels provide lightweight categorization.

Examples

```
Architecture
Research
Documentation
Backend
Frontend
Urgent
Customer Facing
```

Labels are organizational metadata only.

They have no execution semantics.

---

# Milestones

Milestones group Stories into meaningful checkpoints.

Example

```
Promotion Initiative
↓
Milestone
Promotion Packet Complete
↓
Stories
```

Milestones provide progress reporting without affecting execution.

---

# Planning Validation

Before an Initiative becomes executable, planning validation is performed.

Validation includes:
- Missing Story titles
- Empty Tasks
- Circular dependencies
- Missing Acceptance Criteria
- Invalid Constraints
- Missing Capabilities (Structured mode)

Validation failures prevent execution.

---

# Planning Output

The final output of planning is an immutable Planning Graph.

```
Initiative
↓
Epic
↓
Story
↓
Task
↓
Dependencies
↓
Acceptance Criteria
↓
Constraints
```

The Planning Graph becomes the input to the Runtime Engine.

Execution never modifies the Planning Graph.

Instead, runtime creates independent Execution objects that reference the original planning artifacts.

# Planning Graph

The Planning Graph is the immutable representation of an Initiative.

It contains every planning object and their relationships.

The Planning Graph is the only input required by the Runtime Engine.

```
Initiative
    │
    ├── Epics
    │
    ├── Stories
    │      │
    │      ├── Tasks
    │      ├── Acceptance Criteria
    │      └── Dependencies
    │
    ├── Constraints
    │
    └── Metadata
```

The graph contains **intent only**.

No runtime information is stored here.

---

# Planning Normalization

Different planning modes eventually produce the same Planning Graph.

## Structured Planning

```
User
↓
Stories
↓
Tasks
↓
Capabilities
↓
Planning Graph
```

---

## Goal-Oriented Planning

```
Goal
↓
AI Planner
↓
Stories
↓
Tasks
↓
Capabilities
↓
Planning Graph
```

After normalization, the Runtime Engine cannot distinguish how the plan was created.

This guarantees a single execution model.

---

# AI Planning

AI Planning is treated as a planning assistant.

It never executes work.

Responsibilities include:
- suggesting Stories
- suggesting Tasks
- proposing Dependencies
- proposing Capabilities
- estimating complexity
- identifying missing Acceptance Criteria

The user remains responsible for approving the generated plan.

---

## AI Planning Pipeline

```
Goal
↓
Planner
↓
Draft Plan
↓
Human Review
↓
Approved Plan
↓
Planning Graph
```

Every AI-generated plan must pass through human approval before execution.

---

# Planning Review

Planning should support iterative refinement.

Each review cycle consists of:

```
Draft
↓
Review
↓
Feedback
↓
Update
↓
Review
↓
Approved
```

Reviews modify the Planning Graph until it is marked as Ready.

No runtime objects are created during review.

---

# Planning Versioning

Planning is versioned.

Every significant modification creates a new Planning Version.

```
Planning v1
↓
Planning v2
↓
Planning v3
```

Previous versions remain available for comparison and audit.

---

## Version Structure

```
Planning Version
id
initiativeId
versionNumber
createdAt
createdBy
changeSummary
status
```

Only one version may be marked as Active.

---

# Change Management

Planning changes are classified into categories.

Examples

## Structural
- Story added
- Story removed
- Task added
- Dependency removed

---

## Business
- Objective changed
- Acceptance Criteria updated
- Priority changed

---

## Administrative
- Labels updated
- Metadata changed
- Ownership changed

---

# Planning Freeze

Before execution begins, the active Planning Version is frozen.

```
Planning
↓
Ready
↓
Frozen
↓
Execution
```

Execution always references a frozen version.

Planning may continue evolving through a new version.

---

# Replanning

Long-running Initiatives often require replanning.

Instead of modifying the active plan:

```
Planning v1
↓
Execution
↓
Planning v2
↓
Future Execution
```

Existing executions continue using the version they started with.

Future executions use the latest approved version.

This guarantees deterministic execution and reproducibility.

---

# Planning Policies

Organizations may define planning policies.

Examples

```
Every Story requires:
✓ Owner
✓ Estimate
✓ Acceptance Criteria
✓ At least one Task
```

Additional examples

```
Every Initiative
Must contain at least one Epic
Every Task
Must define Priority
Every Story
Requires Review
Every Initiative
Requires Executive Sponsor
```

Policies are validated before execution.

---

# Planning Metrics

Planning metrics provide visibility into plan quality.

Examples

```
Stories
Tasks
Dependencies
Acceptance Criteria
Blocked Stories
Completion Estimate
Coverage
Planning Health
```

These metrics are advisory.

They do not affect runtime behavior.

---

# Planning Health

A Planning Health Score summarizes planning completeness.

Possible inputs include:
- missing acceptance criteria
- unresolved dependencies
- orphan tasks
- missing owners
- missing estimates
- policy violations

Example

```
Planning Health
94%
Warnings
2
Errors
0
```

The score helps identify areas needing refinement before execution.

---

# Planning Commands

Planning is modified through business commands rather than CRUD operations.

Examples

```
Create Initiative
Update Initiative
Create Epic
Create Story
Move Story
Archive Story
Create Task
Split Task
Merge Tasks
Add Dependency
Remove Dependency
Approve Planning
Freeze Planning
Create Planning Version
```

Every command produces one or more domain events.

---

# Planning Events

The Planning subsystem publishes immutable events.

Examples

```
Initiative Created
Epic Created
Story Created
Story Archived
Task Created
Task Updated
Dependency Added
Dependency Removed
Planning Approved
Planning Frozen
Planning Version Created
```

Events provide:
- audit history
- analytics
- synchronization
- future event sourcing support

---

# Planning Invariants

The following invariants must always hold.

## Initiative
- Owns one active Planning Version.
- Contains at least one Epic before execution.
- Cannot execute unless Planning is Frozen.

---

## Epic
- Belongs to exactly one Initiative.
- Cannot exist without its parent Initiative.

---

## Story
- Belongs to exactly one Epic.
- Owns one or more Tasks.
- Defines Acceptance Criteria before execution.

---

## Task
- Belongs to exactly one Story.
- Uses exactly one Planning Mode.
- May depend only on Tasks within the same Story.
- Cannot reference runtime objects.

---

## Dependency
- Must form a Directed Acyclic Graph (DAG).
- Circular dependencies are invalid.
- Referenced Tasks must exist.

---

## Planning Version
- Exactly one Active version per Initiative.
- Frozen versions are immutable.
- Executions always reference a Frozen version.

---

# Planning Architecture Summary

The Planning subsystem is intentionally independent from execution.

Responsibilities:
- capture business intent
- organize work
- validate completeness
- support iterative refinement
- produce an immutable Planning Graph

It intentionally does **not**:
- schedule execution
- invoke providers
- track runtime progress
- manage retries
- store execution logs

Those responsibilities belong entirely to the Runtime subsystem.

By maintaining this strict separation, Leader Control Center ensures that planning remains stable and business-oriented while execution technology can evolve independently.
