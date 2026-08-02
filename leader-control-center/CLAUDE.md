# CLAUDE.md — Leader Control Center

Guidance for Claude Code when working in this repository. Keep it short; the
authoritative detail lives in the specs and docs linked below.

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

1. [`README.md`](README.md) — full product vision, domain model, principles.
2. [`_specs_/`](_specs_) — the spec-kit. Start at [`_specs_/README.md`](_specs_/README.md)
   for reading order and the Concept→Spec index. `_specs_/domain/` is normative.
3. [`_docs_/`](_docs_) — condensed design docs (01-domain, 03-runtime, 05-api,
   08-storage, 09-frontend, …) backing the specs.
4. [`getting-started.md`](getting-started.md) — how to run the stack end to end.

**Spec precedence when sources disagree:** `_specs_/domain/` wins, then root
`README.md`, then everything else.

## Repository layout

- [`backend/`](backend) — FastAPI control-plane API + simulation engine. See
  [`backend/CLAUDE.md`](backend/CLAUDE.md).
- [`frontend/`](frontend) — React supervision console. See
  [`frontend/CLAUDE.md`](frontend/CLAUDE.md).
- `_specs_/`, `_docs_/` — specifications and design docs (source of truth).

## How to start writing code

1. Read the root `README.md` and the relevant `_specs_/` section for the area
   you're touching.
2. Work in the subfolder (`backend/` or `frontend/`) and follow that folder's
   `CLAUDE.md` for setup, run, and test commands.
3. Run the stack per `getting-started.md` and verify behavior before finishing.

## Project-wide rules

- **Stay in this folder.** Do not read or modify anything outside
  `leader-control-center/`.
- **Command-oriented, not CRUD.** The API and UI expose business commands
  (Start, Approve, Retry…), never workflow-engine internals.
- **Engine independence.** Never leak Temporal/engine concepts outside the
  backend `workflow/` package. Business code depends on `workflow/port.py` only.
- **Camel on the wire.** The JSON contract (`backend` snake_case → camelCase)
  must stay in lockstep with `frontend/src/types/domain.ts`.
