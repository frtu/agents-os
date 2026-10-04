# AGENTS.md — Leader Control Center

Guidance for coding agents working in this repository. Keep it short; the
authoritative detail lives in the specs and docs linked below.

## Workflow — spec-first (mandatory)

**Every change that modifies application behaviour starts in `_specs_/` before
any code.** Specs are the source of truth; code and tests are downstream
([constitution](_specs_/constitution.md) P7, P8). The order is non-negotiable:

1. **Spec first.** Create/update `_specs_/features/NNN-short-name/` from
   [`_specs_/_templates/`](_specs_/_templates) — `spec.md` with numbered,
   testable **FR-N**, **User Scenarios**, and **AC-N**; `plan.md` (with its
   **Constitution Check** and **Test Plan**) and `tasks.md` when scope warrants.
   Amend every area spec it touches; a contract change always updates
   [`_specs_/api/rest-api.md`](_specs_/api/rest-api.md) /
   [`realtime.md`](_specs_/api/realtime.md). A principle change amends
   [`_specs_/constitution.md`](_specs_/constitution.md) first, with a version bump.
2. **Then code.** Implement to the spec; cite the requirement in code comments
   (`# spec 002 FR-3`, or `spec planning/schedules D4` for area specs).
3. **Then tests (always).** Land tests in the same change, one per AC, citing the
   id in a comment and the test name (`# spec 002 AC-3` / `test_..._ac3`). Run
   the backend suite and the frontend typecheck/build; a feature is not done
   until they pass ([`_specs_/testing/testing.md`](_specs_/testing/testing.md)).
4. **Keep them in sync.** Spec, code, and tests agree at the end of the change;
   if implementation forces a design change, update the spec. Known code-vs-spec
   gaps go in [`_specs_/clarification.md`](_specs_/clarification.md), never
   silently.

Pure non-behavioural chores (formatting, comment typos, dependency bumps) may
skip step 1. When in doubt, write the spec.

## What this project is

Leader Control Center is a **human-in-the-loop control plane for supervising
durable AI workflows** — a supervision console, *not* a workflow engine, chat
app, or LLM framework. Humans watch running work, answer paused decisions, and
approve/steer; the engine executes.

Core domain (read the specs before changing any of it):

- **Planning (immutable intent):** Portfolio → Initiative → Epic → Story → Task
- **Runtime (disposable):** Story Execution → Task Execution → Capability
  Execution → Provider Execution
- **History is permanent.** Runtime code never mutates planning objects.
- **Capability** = *what* ability · **Execution Strategy** = *how* · **Provider**
  = *who* (OpenAI/Anthropic/Human/MCP/Temporal), interchangeable.
- **Every pause is a Human Request; every Human Request yields exactly one
  Decision.** The Attention Queue is the global list of open Human Requests.

## Where the truth lives (read in this order)

1. [`_specs_/constitution.md`](_specs_/constitution.md) — ratified principles;
   every plan carries a Constitution Check against it.
2. [`README.md`](README.md) — full product vision, domain model, principles.
3. [`_specs_/`](_specs_) — the spec-kit. Start at [`_specs_/README.md`](_specs_/README.md)
   for reading order and the Concept→Spec index. `_specs_/domain/` is normative;
   `_specs_/features/` holds the per-feature spec → plan → tasks.
4. [`_docs_/`](_docs_) — condensed design docs (01-domain, 03-runtime, 05-api,
   08-storage, 09-frontend, …) backing the specs.
5. [`getting-started.md`](getting-started.md) — how to run the stack end to end.

**Spec precedence when sources disagree:** `_specs_/constitution.md` wins, then
`_specs_/domain/`, then root `README.md`, then the later feature spec, then
everything else.

## Repository layout

- [`backend/`](backend) — FastAPI control-plane API + simulation engine. See
  [`backend/AGENTS.md`](backend/AGENTS.md).
- [`frontend/`](frontend) — React supervision console. See
  [`frontend/AGENTS.md`](frontend/AGENTS.md).
- `_specs_/`, `_docs_/` — specifications and design docs (source of truth).

## How to start writing code

1. Read the constitution, the root `README.md`, and the relevant `_specs_/`
   section for the area you're touching.
2. Write or update the feature spec (see **Workflow** above).
3. Work in the subfolder (`backend/` or `frontend/`) and follow that folder's
   `AGENTS.md` for setup, run, and test commands.
4. Add tests mapped to the ACs; run the stack per `getting-started.md` and
   verify behavior before finishing.

## Project-wide rules

- **Stay in this folder.** Do not read or modify anything outside
  `leader-control-center/`.
- **Dependencies on demand.** External services (Temporal, in
  [`_infra_/docker-temporal`](_infra_/docker-temporal)) are listed in
  [`backend/README.md` → Dependencies](backend/README.md#dependencies). Start
  them yourself when a task needs them, and stop them when finished unless the
  user wants them left running. To call their APIs, see
  [`backend/dependencies.md`](backend/dependencies.md). The simulation engine
  needs no dependencies.
- **Command-oriented, not CRUD.** The API and UI expose business commands
  (Start, Approve, Retry…), never workflow-engine internals.
- **Engine independence.** Never leak Temporal/engine concepts outside the
  backend `workflow/` package. Business code depends on `workflow/port.py` only.
- **Camel on the wire.** The JSON contract (`backend` snake_case → camelCase)
  must stay in lockstep with `frontend/src/types/domain.ts`.
