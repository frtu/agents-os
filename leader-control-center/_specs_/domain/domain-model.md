# Domain Model

This is the canonical domain model. All other specs derive from it. It follows
the README hierarchy: **Portfolio → Initiative → Epic → Story → Task**, with a
separate but linked **Runtime** side.

> Planning is immutable. Runtime is disposable. History is permanent.

---

## Two Perspectives

Leader Control Center separates presentation from implementation.

### Human View

The leader supervises **Initiatives**. Everything they need is grouped under an
Initiative: planning, progress, executions, waiting approvals, artifacts,
history.

```
Workspace → Initiative → Current Progress → Decisions → Artifacts
```

### System View

Internally an Initiative is composed of a stable planning hierarchy and an
independent runtime.

```
Workspace → Epic → Story → Task → Execution → Capability Execution → Provider Execution
```

The mapping between the two:

| Human View   | Internal Domain                  |
| ------------ | -------------------------------- |
| Initiative   | Epic + Runtime                   |
| Progress     | Story Executions                 |
| Running Work | Task Executions                  |
| AI Activity  | Capability / Provider Executions |
| Decisions    | Human Requests + Decisions       |
| Outputs      | Artifacts                        |
| History      | Timeline                         |

---

## Aggregate Structure

```
Portfolio
│
└── Initiative (Human View)
      │
      ├── Planning  (immutable intent)
      │     ├── Epic
      │     │     └── Story
      │     │           ├── Task
      │     │           ├── Dependency
      │     │           └── Acceptance Criteria
      │     └── Planning Metadata
      │
      └── Runtime  (disposable execution)
            ├── Story Execution
            │     ├── Task Execution
            │     │     ├── Capability Execution
            │     │     │     ├── Provider Execution
            │     │     │     ├── Provider Execution
            │     │     │     └── Provider Execution
            │     │     ├── Timeline
            │     │     ├── Human Requests
            │     │     ├── Decisions
            │     │     └── Artifacts
            │     └── Metrics
            └── Attention Queue
```

Aggregate roots and their consistency boundaries are defined in
[bounded-contexts.md](./bounded-contexts.md).

---

## Planning Entities

### Portfolio
Top-level organizational boundary backed by a `Workspace`. Owns Initiatives,
Users, Providers, Credentials, the Capability Catalog, Integrations, and default
AI configuration. MVP assumes a single Portfolio.

### Initiative
The primary business object presented to leaders; represents a business outcome.
Groups planning, runtime, decisions, artifacts, and history. Backed internally
by one or more Epics together with their runtime executions.

### Epic
Primary planning container grouping Stories that contribute to one Initiative.
Achievable in roughly one month. Implementation detail — leaders interact with
Initiatives, not Epics.

### Story
A business deliverable (e.g. "Write promotion document", "Create architecture
proposal"). Progresses through the planning board and owns one or more Tasks,
Dependencies, and Acceptance Criteria.

### Task
A unit of planned work. Defines **what** should be accomplished; **never how**.
Execution decisions are deferred to runtime. Every Task is created in exactly one
**Planning Mode** (see [../planning/planning-modes.md](../planning/planning-modes.md)):

- **Structured** — leader specifies Capability, dependencies, acceptance criteria.
- **Goal-Oriented** — leader specifies a goal + success criteria; the AI planner
  decomposes it.

Both modes normalize into the same execution model.

### Dependency
A prerequisite relationship between Tasks. Informational in MVP; enables
Dependency Scheduling later.

### Acceptance Criteria
Conditions defining completion for a Story (and optionally a Task).

---

## Catalog Entities (Portfolio-level)

### Capability
A stable, provider-independent business ability (Research, Write, Review, Code,
Diagram, Summarize…). Shape:

```
Capability { id, name, description, inputs, outputs, supportedProviders }
```

See [../planning/capabilities.md](../planning/capabilities.md).

### Provider
An interchangeable implementation that executes Capabilities via a common
contract. Examples: OpenAI, Anthropic, Gemini, Claude Code, Cursor, GitHub MCP,
Slack MCP, Temporal Activity, Human. See
[../execution/providers.md](../execution/providers.md).

### Workflow Definition
A reusable **blueprint** (authoring-time DSL) that governs how work is created.
Shape:

```
WorkflowDefinition { id, name, input, definition }
```

- `input` is a JSON Schema describing the parameters an instance requires.
- `definition` is the DSL body realizing the workflow.

An Initiative may optionally reference a Workflow Definition; a Story created from
a template references one and captures `templateInput` validated against its
`input` schema. A Workflow Definition is **not** the Temporal Workflow Engine
(which executes runtime work behind a port, see
[../workflow-engine/workflow-engine.md](../workflow-engine/workflow-engine.md)) —
it is Portfolio-level catalog intent, like Capability.

---

## Runtime Entities

Planning creates runtime objects; planning itself is never modified.

```
Planning → Execution → History
```

### Story Execution
One runtime instance of a Story. Orchestrates Task Executions, aggregates status
and artifacts, exposes the Story timeline.

### Task Execution
One runtime instance of a Task. Invokes capabilities, monitors execution,
requests human interaction, publishes runtime events. A Task may execute multiple
times without modifying planning.

### Capability Execution
Represents **what ability is required** for a Task Execution. Runs exactly one
**Execution Strategy** (see
[../execution/execution-strategy.md](../execution/execution-strategy.md)).

### Provider Execution
Represents the concrete run against one Provider. One Capability Execution may
produce several Provider Executions (e.g. Parallel, Consensus). A Provider
failure does not necessarily imply a Capability failure — the Execution Strategy
decides.

---

## Supporting Runtime Objects

- **Human Request** — pauses execution pending human attention. See
  [../execution/human-requests.md](../execution/human-requests.md).
- **Decision** — the immutable human response resolving a Human Request.
- **Artifact** — immutable, versioned output. See
  [../execution/artifacts.md](../execution/artifacts.md).
- **Timeline** — append-only event history. See [event-model.md](./event-model.md).
- **Attention Queue** — cross-Initiative aggregation of items needing attention.

---

## Core Invariants

1. Runtime never mutates Planning.
2. Planning never depends on Runtime.
3. Every Human Request resolves to exactly one Decision.
4. Artifacts and Timeline events are immutable; updates create new versions/events.
5. Only a **Ready** Task may be started.
6. A Capability is resolved to Providers only at runtime, via an Execution
   Strategy — never fixed at planning time.

State machines for every entity are in [state-machines.md](./state-machines.md).
