# User Stories

Supervision-centric stories for the primary user (a **leader**). Each maps to
capabilities defined elsewhere in the spec-kit.

---

## Planning

**Organize work into Initiatives**
As a leader, I want to organize work into Initiatives so related outcomes stay
grouped. → [../domain/domain-model.md](../domain/domain-model.md)

**Plan Stories and Tasks**
As a leader, I want to define Stories and break them into Tasks so AI can execute
smaller units of work. → [../planning/planning-model.md](../planning/planning-model.md)

**Choose how a Task is planned**
As a leader, I want to define a Task by picking a Capability (Structured) or, in
the future, by stating a goal (Goal-Oriented). →
[../planning/planning-modes.md](../planning/planning-modes.md)

---

## Execution

**Manually start work (MVP)**
As a leader, I want to manually start Tasks so I stay in control of execution. →
[../planning/scheduling.md](../planning/scheduling.md)

**Monitor everything running**
As a leader, I want to monitor every running execution so I know what AI is
doing. → [../frontend/frontend.md](../frontend/frontend.md)

**Retry without re-planning**
As a leader, I want to retry failed executions without recreating planning. →
[../execution/execution-model.md](../execution/execution-model.md)

---

## Human-in-the-loop

**Be interrupted only when necessary**
As a leader, I want AI to stop only when it needs me, so interruptions stay
minimal. → [../execution/human-requests.md](../execution/human-requests.md)

**Handle all decisions in one place**
As a leader, I want every workflow needing attention grouped together so I never
miss an important decision. →
[../execution/human-requests.md](../execution/human-requests.md)

---

## Outputs & History

**Review artifacts before continuing**
As a leader, I want to inspect outputs before approving continuation. →
[../execution/artifacts.md](../execution/artifacts.md)

**Understand what happened**
As a leader, I want to understand everything that happened without reading entire
conversations. → [../domain/event-model.md](../domain/event-model.md)

---

## Acceptance (per story)

Every story is "done" only when its capability is an **explicit** operation in
the API and its business rules are testable **without** Temporal. See
[../overview/roadmap.md](../overview/roadmap.md) and
[../observability/observability.md](../observability/observability.md).
