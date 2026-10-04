# Leader Control Center Constitution

The non-negotiable principles for **Leader Control Center** — a human-in-the-loop
control plane for supervising durable AI workflows. Every spec, plan, task, and
change in this repository MUST comply. When a plan conflicts with the
constitution, the constitution wins; amend the constitution deliberately rather
than working around it.

Version: 1.0.0 · Ratified: 2026-10-04 · Last amended: 2026-10-04

> **1.0.0 (2026-10-04) — Ratified.** Consolidates the product principles
> ([overview/principles.md](./overview/principles.md)), the project rules in
> `AGENTS.md`, and the development model adopted from the sibling
> `leader-assistant` project (spec-first workflow, FR/AC traceability, error
> transparency). No existing spec changed meaning.

---

## Principle 1 — Human first; every pause is a Human Request

Humans own planning, priorities, approvals, clarifications, and strategic
decisions; AI executes. Execution pauses **only** through an explicit
**Human Request**, and every Human Request yields **exactly one** immutable
**Decision**. The Attention Queue is the global list of open Human Requests.

- No hidden waits: a run that needs a human surfaces a Human Request, never a
  silent stall.
- A Decision is traceable to a user, timestamp, execution, and reason.

Source specs: [execution/human-requests.md](./execution/human-requests.md),
[domain/state-machines.md](./domain/state-machines.md).

## Principle 2 — Planning is immutable, Runtime is disposable, History is permanent

Planning (Portfolio → Initiative → Epic → Story → Task) states intent. Runtime
(Story → Task → Capability → Provider Execution) records attempts. History
records what happened.

- Runtime code MUST NEVER mutate planning objects. Retry creates a new
  execution; a Completed Story is never re-opened.
- The Timeline is append-only; existing entries are never edited.
- Artifacts are immutable; an update creates a new version.

Source specs: [domain/domain-model.md](./domain/domain-model.md),
[domain/bounded-contexts.md](./domain/bounded-contexts.md),
[domain/event-model.md](./domain/event-model.md),
[execution/artifacts.md](./execution/artifacts.md).

## Principle 3 — Business first; command-oriented surfaces

The platform models business outcomes. The API and UI expose **business
commands** (Start, Approve, Retry, Pause…) and **projections** (read models),
never CRUD over aggregates and never workflow-engine internals. Catalog data
(Workflow / Activity Definitions) is the one documented exception and is edited
directly.

- HTTP routers are thin: they call the application facade (`ControlCenter`)
  and nothing else.
- The leader never needs to know a workflow-engine concept to use the product.

Source specs: [api/rest-api.md](./api/rest-api.md),
[backend/services-and-commands.md](./backend/services-and-commands.md).

## Principle 4 — Engine independence

The workflow engine (Temporal, the SimulationEngine, any future adapter) is an
implementation detail behind a port.

- Engine concepts (WorkflowId, RunId, Activity, task queue, `temporalio`) MUST
  NOT appear outside the backend `workflow/` package, in the JSON contract, or
  in the realtime stream.
- Business code depends on `workflow/port.py` (and `workflow/scheduler_port.py`)
  only. Swapping an adapter MUST NOT change application, domain, API, or UI
  code.
- Business logic that must run identically on every adapter (e.g. Schedule
  overlap and catch-up) lives in the application layer, not in adapters.

Source specs: [workflow-engine/workflow-engine.md](./workflow-engine/workflow-engine.md),
[planning/schedules.md](./planning/schedules.md) (D2, D5).

## Principle 5 — Provider independence

**Capability** = *what* ability · **Execution Strategy** = *how* it runs ·
**Provider** = *who* runs it. Capabilities never depend on a specific provider;
providers (OpenAI, Anthropic, Human, MCP, Temporal) are interchangeable. "Agent"
is not a domain term.

Source specs: [planning/capabilities.md](./planning/capabilities.md),
[execution/execution-strategy.md](./execution/execution-strategy.md),
[execution/providers.md](./execution/providers.md).

## Principle 6 — Contract lockstep

The wire contract is one contract, owned by the spec.

- JSON is camelCase on the wire; Python stays snake_case (`domain/models.py`
  alias generator).
- `backend/app/domain/models.py`, `frontend/src/types/domain.ts`, and
  [api/rest-api.md](./api/rest-api.md) / [api/realtime.md](./api/realtime.md)
  MUST change in the same change set.
- Every resource carries the envelope `id · version · createdAt · updatedAt`;
  errors are Problem+JSON.

Source specs: [api/rest-api.md](./api/rest-api.md),
[database/data-model.md](./database/data-model.md),
[frontend/frontend.md](./frontend/frontend.md).

## Principle 7 — Spec first; specs are the source of truth

Every behavioural change starts in `_specs_/`, then code, then tests — in the
same change. Code and tests are downstream of the spec; if implementation forces
a design change, the spec is updated rather than left to drift.

- Requirements are numbered and testable (**FR-N**), with **Acceptance
  Criteria** (**AC-N**).
- Code comments and test names cite the requirement they satisfy
  (e.g. `spec 002 FR-3`, `test_..._fr3`).
- Precedence when sources disagree: this constitution → `_specs_/domain/` →
  root `README.md` → later feature spec → everything else.

Source specs: [README.md](./README.md), [testing/testing.md](./testing/testing.md),
[features/README.md](./features/README.md).

## Principle 8 — Tested or not done

A feature or behavioural fix is done only when it lands with automated tests
that map back to its FR/AC ids, and the suite passes. Every invariant in this
constitution maps to at least one automated test
([testing/testing.md](./testing/testing.md) §1).

- Tests run offline and deterministically: no Temporal, no network, no real
  clock unless the test is an explicitly opt-in integration test.
- Time-driven logic takes an injected clock; engine-driven logic is tested
  against a fake port.

Source specs: [testing/testing.md](./testing/testing.md).

## Principle 9 — Error transparency

Errors MUST be surfaced with meaningful context, never silently swallowed or
replaced with unrelated messages.

- **Preserve the reason** — a caught exception's message reaches the
  Problem+JSON `detail`, the Timeline, or the Schedule Run reason.
- **Surface failures in fallbacks** — when a primary path fails and the system
  falls back (e.g. the LLM story-draft falls back to the heuristic stub), the
  response says *what failed and why*, not just the fallback result.
- **Never mask root causes** — a generic message is acceptable only when the
  real error contains secrets; otherwise propagate specifics.
- **Log for diagnostics** — handled errors are still logged at an appropriate
  level.

A leader supervising work (P1) cannot decide well without knowing what actually
happened.

Source specs: [observability/observability.md](./observability/observability.md).

## Principle 10 — Progressive automation, simplest thing first

Every autonomous behaviour first exists as an explicit, human-driven capability
(Manual → Dependency → AI → Autonomous). Build the simplest system that supports
today's workflow while making tomorrow's automation a configuration change, not
an architectural rewrite.

Source specs: [overview/principles.md](./overview/principles.md),
[planning/scheduling.md](./planning/scheduling.md),
[overview/roadmap.md](./overview/roadmap.md).

## Principle 11 — Ubiquitous language

Terms are defined once in [overview/glossary.md](./overview/glossary.md) and
used verbatim in specs, code, API, and UI. Where a UI label differs from the
domain term (e.g. UI "Tasks" = Activity Definitions, UI "Story" = Execution),
the spec states the mapping explicitly.

Source specs: [overview/glossary.md](./overview/glossary.md).

---

## Amendment process

Amendments require: (1) a stated rationale, (2) a version bump (semver: MAJOR
for principle removal/redefinition, MINOR for a new principle, PATCH for
clarifications), and (3) a list of downstream specs to reconcile. Record the
amendment as a note at the top of this file.

## Compliance

Every feature `plan.md` MUST include a **Constitution Check** confirming
alignment with each principle (or justifying a deviation). Reviews reject work
that violates a principle without an approved amendment. Known deviations in the
current code and open questions are tracked in
[clarification.md](./clarification.md).
