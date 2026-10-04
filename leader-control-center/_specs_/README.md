# Leader Control Center — Spec-Kit

Development specifications for **Leader Control Center**, a human-in-the-loop
control plane for supervising durable AI workflows.

This spec-kit is the implementation guide. The root
[../README.md](../README.md) holds the product vision; the specs here turn it
into buildable, aligned, non-contradictory specifications.

---

## How to Read

Start here, then follow the reading order:

0. **[constitution.md](./constitution.md)** — the ratified, versioned principles
   every spec, plan, and change is checked against.
1. **overview/** — why the product exists and the shared language.
2. **domain/** — the canonical model everything else derives from.
3. **planning/** — how intent is expressed (stable).
4. **execution/** — how intent is fulfilled at runtime (disposable).
5. **workflow-engine/** — how runtime maps onto Temporal (hidden behind a port).
6. **backend/ · api/ · database/** — how the backend is built.
7. **frontend/** — how leaders supervise.
8. **auth/ · permissions/ · notifications/ · observability/ · deployment/** —
   cross-cutting concerns (MVP depth).
9. **testing/** — invariant test matrix and acceptance gate.
10. **features/** — the buildable layer: `NNN-*/spec.md → plan.md → tasks.md`.

If two documents ever disagree: the **constitution** wins, then **domain/**,
then the root README, then the later feature spec. Open questions and known
code-vs-spec deviations live in [clarification.md](./clarification.md).

---

## Folder Map

```
_specs_/
  constitution.md ratified principles (versioned) — the compliance gate
  clarification.md open questions · known deviations (code lags spec)
  _templates/     spec-template · plan-template · tasks-template
  features/       NNN-<feature>/ spec.md · plan.md · tasks.md
  testing/        testing (invariant matrix, levels, acceptance gate)
  overview/       vision · principles · roadmap · glossary · user-stories
  domain/         domain-model · state-machines · bounded-contexts · event-model
  planning/       planning-model · planning-modes · capabilities · scheduling ·
                  schedules
  execution/      execution-model · execution-strategy · providers ·
                  human-requests · artifacts · activity-definitions
  workflow-engine/ workflow-engine
  backend/        architecture · services-and-commands
  api/            rest-api · realtime
  database/       data-model
  frontend/       frontend
  auth/           auth
  permissions/    permissions
  notifications/  notifications
  observability/  observability (+ NFRs)
  deployment/     deployment
```

---

## Core Model at a Glance

Planning is immutable. Runtime is disposable. History is permanent.

```
Portfolio → Initiative → Epic → Story → Task            (planning intent)
                                   │
                                   ▼
Story Execution → Task Execution → Capability Execution → Provider Execution   (runtime)
```

- **Capability** = *what* ability is required (stable, provider-independent).
- **Execution Strategy** = *how* it runs (Single/Retry/Parallel/Consensus/…).
- **Provider** = *who* runs it (OpenAI/Anthropic/Human/MCP/…), interchangeable.
- Execution pauses only via **Human Requests**, each resolved by one **Decision**.

Full detail: [domain/domain-model.md](./domain/domain-model.md).

---

## Concept → Spec Index

| Root README concept | Spec |
| ------------------- | ---- |
| Vision / Goals / Non-Goals | [overview/vision.md](./overview/vision.md) |
| Product Principles | [overview/principles.md](./overview/principles.md) |
| Domain Model / Human View vs System View | [domain/domain-model.md](./domain/domain-model.md) |
| State Machines | [domain/state-machines.md](./domain/state-machines.md) |
| Timeline / Events | [domain/event-model.md](./domain/event-model.md) |
| Planning Modes (Structured / Goal-Oriented) | [planning/planning-modes.md](./planning/planning-modes.md) |
| Capability Model / Catalog | [planning/capabilities.md](./planning/capabilities.md) |
| Workflow Definition (blueprint/template) | [domain/domain-model.md](./domain/domain-model.md) · [database/data-model.md](./database/data-model.md) · [api/rest-api.md](./api/rest-api.md) · [frontend/frontend.md](./frontend/frontend.md) |
| Scheduling (Manual / Dependency / AI) | [planning/scheduling.md](./planning/scheduling.md) |
| Schedules (time-triggered Stories: once / interval / cron) | [planning/schedules.md](./planning/schedules.md) |
| Runtime Objects / Execution | [execution/execution-model.md](./execution/execution-model.md) |
| Execution Strategy | [execution/execution-strategy.md](./execution/execution-strategy.md) |
| Provider Model | [execution/providers.md](./execution/providers.md) |
| Activity Definitions (UI "Tasks": bash / webhook building blocks) | [execution/activity-definitions.md](./execution/activity-definitions.md) |
| Human Requests / Decisions / Attention Queue | [execution/human-requests.md](./execution/human-requests.md) |
| Artifact Model | [execution/artifacts.md](./execution/artifacts.md) |
| Architecture | [backend/architecture.md](./backend/architecture.md) |
| Workflow Engine / Temporal | [workflow-engine/workflow-engine.md](./workflow-engine/workflow-engine.md) |
| API Philosophy | [api/rest-api.md](./api/rest-api.md) · [api/realtime.md](./api/realtime.md) |
| Technology Stack | [backend/architecture.md](./backend/architecture.md) · [frontend/frontend.md](./frontend/frontend.md) |
| User Interface (Kanban / drawers) | [frontend/frontend.md](./frontend/frontend.md) |
| MVP Scope / Future Evolution | [overview/roadmap.md](./overview/roadmap.md) |

---

## MVP Build Order (suggested)

1. Domain model + state machines + event log (domain/, database/).
2. Planning commands + REST (Structured mode only).
3. Manual scheduling + Single-Provider execution via Temporal adapter.
4. Timeline + Attention Queue projections + WebSocket.
5. Frontend: Initiative Kanban, Story/Task detail, Attention Queue.
6. Human Requests / Decisions end-to-end.
7. Artifact viewing.

Scope and phase gates: [overview/roadmap.md](./overview/roadmap.md).

---

## Development Model (spec-first)

Every behavioural change follows **spec → code → tests**, in one change set
([constitution](./constitution.md) P7, P8):

1. **Spec.** Create `features/NNN-short-name/` from [`_templates/`](./_templates)
   (`spec.md` with numbered **FR-N**, User Scenarios, **AC-N**; plus `plan.md`
   with a Constitution Check and Test Plan, and `tasks.md`, when scope warrants).
   Amend the area specs it touches — always `api/rest-api.md` /
   `api/realtime.md` for a contract change. A principle change amends
   `constitution.md` first, with a version bump.
2. **Code.** Implement to the spec; cite requirements in comments
   (`# spec 002 FR-3`).
3. **Tests.** Land tests in the same change, one per AC, named/commented with the
   id (`test_…_ac3`, `# spec 002 AC-3`). See [testing/testing.md](./testing/testing.md).
4. **Sync.** Spec, code, and tests agree at the end; if the implementation forced
   a design change, update the spec.

Pure chores (formatting, typos, dependency bumps) may skip step 1. Feature
conventions: [features/README.md](./features/README.md).

---

## Conventions

- Ubiquitous language is defined once in
  [overview/glossary.md](./overview/glossary.md) and used verbatim in code, API,
  and UI.
- "Agent" is not a domain term — the runtime uses **Capability** + **Provider**.
- Cross-cutting specs (auth, permissions, notifications, observability,
  deployment) are intentionally MVP-depth; their bounded-context boundaries are
  fixed so growth is additive.
