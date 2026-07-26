# Product Principles

These principles constrain every design and implementation decision in the
spec-kit. When a trade-off is unclear, resolve it in favor of these principles.

---

## Human First

Humans remain responsible for:

- planning
- priorities
- approvals
- clarifications
- strategic decisions

AI is responsible for execution. The system pauses execution **only** through
explicit [Human Requests](../execution/human-requests.md).

---

## Business First

The platform models **business outcomes**. Workflow engines, LLMs, MCP servers,
and providers are implementation details hidden behind the execution layer. The
leader never needs to understand workflow-engine concepts.

---

## Human View ≠ System View

Leaders think in terms of **Initiatives** (business outcomes such as "Platform
Modernization" or "AI Adoption"). Internally, planning is represented with
familiar **Epic / Story / Task** concepts.

| Human View   | Internal Domain            |
| ------------ | -------------------------- |
| Initiative   | Epic + Runtime             |
| Progress     | Story Executions           |
| Running Work | Task Executions            |
| AI Activity  | Capability / Provider Executions |
| Decisions    | Human Requests + Decisions |
| Outputs      | Artifacts                  |
| History      | Timeline                   |

This separation gives a business-centric experience over a clean, extensible
planning model.

---

## Planning ≠ Runtime

Planning defines **what should happen**. Runtime records **what is happening**.

- Planning stays stable throughout execution.
- Executions may retry, fail, pause, resume, or restart **without modifying
  planning**.

```
Planning   →  immutable intent
Runtime    →  disposable execution
History    →  permanent record
```

---

## Progressive Automation

Every autonomous capability must first exist as an **explicit** capability.
Users can always choose their level of autonomy without changing the
architecture:

```
Explicit Planning → AI-Assisted Planning → Fully Autonomous Planning
```

The scheduling evolution path:

```
Leader
  ↓
Manual Scheduling (MVP)
  ↓
Dependency Scheduling
  ↓
AI Planning
  ↓
Autonomous Coordination
```

See [../planning/scheduling.md](../planning/scheduling.md) and
[../planning/planning-modes.md](../planning/planning-modes.md).

---

## Provider Independence

**Capabilities** are stable business concepts (Research, Write, Review, Code).
**Providers** (OpenAI, Anthropic, Gemini, Claude Code, Human, MCP servers) are
interchangeable implementations. Capabilities never depend on a specific
provider, and the backend never leaks provider or workflow-engine concepts to
the frontend.

---

## Immutability & Auditability

- **Artifacts** are immutable; updates create new versions.
- The **Timeline** is append-only; history is never modified.
- Every **Decision** is traceable to a user, timestamp, execution, and reason.

---

## Guiding Principle

> Build the simplest system that supports today's workflow while making
> tomorrow's automation a configuration change rather than an architectural
> rewrite.
