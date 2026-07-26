# Glossary — Ubiquitous Language

A shared vocabulary used consistently across specs, code, API, and UI. Terms are
grouped by bounded context (see
[../domain/bounded-contexts.md](../domain/bounded-contexts.md)).

---

## Organization

| Term | Definition |
| ---- | ---------- |
| **Portfolio** | Top-level organizational boundary, backed by a Workspace. Owns Initiatives, Users, Providers, Credentials, the Capability Catalog, Integrations, and default AI configuration. MVP assumes a single Portfolio. |
| **Workspace** | The technical/isolation unit backing a Portfolio. |
| **User** | A person acting within a Portfolio (leader, reviewer). |

---

## Planning (Human View)

| Term | Definition |
| ---- | ---------- |
| **Initiative** | The primary business object presented to leaders; represents a business outcome (e.g. "Platform Modernization"). Backed internally by one or more Epics plus their runtime. |
| **Attention Queue** | Aggregated, cross-Initiative list of items needing human attention. |

---

## Planning (Internal Model)

| Term | Definition |
| ---- | ---------- |
| **Epic** | Primary planning container grouping Stories toward one Initiative. Roughly one month of work. Implementation detail; leaders see the Initiative. |
| **Story** | A business deliverable (e.g. "Write promotion document"). Owns Tasks, Dependencies, Acceptance Criteria. |
| **Task** | A unit of planned work. Defines **what** to accomplish, never **how**. Created in exactly one Planning Mode. |
| **Planning Mode** | How a Task expresses intent: **Structured** (explicit capability) or **Goal-Oriented** (a goal the AI planner decomposes). |
| **Dependency** | A prerequisite relationship between Tasks. Informational in MVP; enables scheduling later. |
| **Acceptance Criteria** | Conditions defining completion for a Story or Task. |
| **Capability** | A stable business ability the platform can perform (Research, Write, Review, Code…). Provider-independent. |
| **Capability Catalog** | The reusable set of Capabilities managed at Portfolio/Workspace level. |

---

## Runtime

| Term | Definition |
| ---- | ---------- |
| **Story Execution** | One runtime instance of a Story. Orchestrates Task Executions; aggregates status and artifacts. |
| **Task Execution** | One runtime instance of a Task. Invokes capabilities, requests human interaction, publishes events. A Task may execute many times. |
| **Capability Execution** | Runtime resolution of *what ability is required* for a Task Execution. Runs one Execution Strategy. |
| **Provider Execution** | The concrete run against one Provider (OpenAI, Anthropic, Human, MCP…). One Capability Execution may spawn several. |
| **Execution Strategy** | *How* a Capability is executed across Providers: Single, Retry, Parallel, Consensus, Human Review, Pipeline, Loop, Fan-Out. |
| **Provider** | An interchangeable implementation that executes Capabilities via a common contract (`supports/estimate/execute/cancel/resume`). |
| **Scheduling Strategy** | Policy deciding *when* Tasks start: Manual (MVP), Dependency, AI Planning. |

---

## Human Interaction

| Term | Definition |
| ---- | ---------- |
| **Human Request** | A first-class runtime object representing something requiring human attention (Approval, Clarification, Budget, Tool Permission, Missing Information, Choose Option, Risk Acceptance). |
| **Decision** | The human response to a Human Request (Approve, Reject, Clarify, Continue, Abort, Retry, Select Option). Exactly one Decision resolves one Human Request. Immutable. |

---

## Outputs & History

| Term | Definition |
| ---- | ---------- |
| **Artifact** | A first-class, immutable, versioned output (Markdown, Diagram, PDF, Spreadsheet, Presentation, Source Code, Test Report…). |
| **Timeline** | The append-only sequence of immutable events for an execution. |
| **Event** | An immutable fact recording that something happened. Source of truth for read models. |
| **Notification** | A transient surfaced event for user awareness (distinct from a Human Request, which blocks execution). |

---

## Invariants (naming rules)

- Planning terms (Epic/Story/Task) are **never** used for runtime objects.
- Runtime terms always carry the `Execution` suffix.
- "Agent" is **not** a domain term; the runtime uses **Capability** +
  **Provider**. (Any external "agent" is modeled as a Provider.)
