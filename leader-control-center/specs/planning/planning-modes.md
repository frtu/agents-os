# Planning Modes

Leader Control Center intentionally separates **planning** (business intent) from
**execution** (how intent is fulfilled). Every Task is created using exactly one
Planning Mode.

```
Planning Mode
├── Structured
└── Goal-Oriented
```

Both modes normalize into the same execution model, so users can progressively
adopt AI planning without changing the runtime architecture.

---

## Structured Planning (default, MVP)

The leader explicitly defines:

- Task name
- **Capability** (from the Catalog)
- Dependencies
- Acceptance Criteria

Example:

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

Predictable and deterministic. Recommended for production workflows and the only
mode in the MVP.

---

## Goal-Oriented Planning (future)

The leader describes the desired outcome instead of choosing a Capability. The
**AI Planner** decomposes it.

Example:

```
Goal
  Prepare a promotion package that demonstrates my technical
  leadership and business impact.
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

**before** execution begins. The output is a set of Structured Tasks the leader
can review — meaning Goal-Oriented planning *produces* Structured planning, never
bypasses it.

---

## Normalization

Regardless of mode, a Task resolves to the same runtime shape:

```
Task → Task Execution → Capability Execution → Provider Execution
```

- **Structured:** capability is known at planning time.
- **Goal-Oriented:** capability is derived by the planner, then executed
  identically.

This is why increasing autonomy is a configuration change, not a rewrite.

---

## Progressive Planning

The application supports increasing levels of autonomy:

```
Structured
  ↓
AI Suggestions        # planner proposes tasks/capabilities; leader approves
  ↓
Goal-Oriented         # leader states goal; planner decomposes
  ↓
Autonomous Planning   # planner plans + launches within guardrails
```

Each step reuses the same domain model and execution model. See
[../overview/roadmap.md](../overview/roadmap.md).

---

## Guardrails (all modes)

- AI-proposed plans are **Draft** until a human marks them **Ready**
  (Human First principle).
- Goal-Oriented and Autonomous modes must still emit explicit Capabilities so
  the runtime and audit trail remain provider-independent and inspectable.
