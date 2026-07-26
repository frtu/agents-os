# Leader Control Center — Spec-Kit

Development specifications for **Leader Control Center**, a human-in-the-loop
control plane for supervising durable AI workflows.

This spec-kit is the implementation guide. The root
[../README.md](../README.md) holds the product vision; the specs here turn it
into buildable, aligned, non-contradictory specifications.

---

## How to Read

Start here, then follow the reading order:

1. **overview/** — why the product exists and the shared language.
2. **domain/** — the canonical model everything else derives from.
3. **planning/** — how intent is expressed (stable).
4. **execution/** — how intent is fulfilled at runtime (disposable).
5. **workflow-engine/** — how runtime maps onto Temporal (hidden behind a port).
6. **backend/ · api/ · database/** — how the backend is built.
7. **frontend/** — how leaders supervise.
8. **auth/ · permissions/ · notifications/ · observability/ · deployment/** —
   cross-cutting concerns (MVP depth).

If two documents ever disagree, **domain/** wins, then the root README.

---

## Folder Map

```
specs/
  overview/       vision · principles · roadmap · glossary · user-stories
  domain/         domain-model · state-machines · bounded-contexts · event-model
  planning/       planning-model · planning-modes · capabilities · scheduling
  execution/      execution-model · execution-strategy · providers ·
                  human-requests · artifacts
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
| Scheduling (Manual / Dependency / AI) | [planning/scheduling.md](./planning/scheduling.md) |
| Runtime Objects / Execution | [execution/execution-model.md](./execution/execution-model.md) |
| Execution Strategy | [execution/execution-strategy.md](./execution/execution-strategy.md) |
| Provider Model | [execution/providers.md](./execution/providers.md) |
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

## Conventions

- Ubiquitous language is defined once in
  [overview/glossary.md](./overview/glossary.md) and used verbatim in code, API,
  and UI.
- "Agent" is not a domain term — the runtime uses **Capability** + **Provider**.
- Cross-cutting specs (auth, permissions, notifications, observability,
  deployment) are intentionally MVP-depth; their bounded-context boundaries are
  fixed so growth is additive.
