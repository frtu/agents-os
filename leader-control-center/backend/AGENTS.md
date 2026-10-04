# AGENTS.md — Backend

FastAPI control-plane API + simulation engine for the Leader Control Center.
Read this repo's root [`../AGENTS.md`](../AGENTS.md) first for the domain model
and project rules.

## Docs & specs

- **Constitution + spec-first workflow:** [`../_specs_/constitution.md`](../_specs_/constitution.md)
  · root [`../AGENTS.md`](../AGENTS.md#workflow--spec-first-mandatory). Spec →
  code → tests, in one change.
- Testing model (invariant matrix, levels, gate): [`../_specs_/testing/testing.md`](../_specs_/testing/testing.md)

- Backend overview, architecture, endpoints, config: [`README.md`](README.md)
- Storage (SQLite overlay on the data model): [`storage.md`](storage.md)
- **External service APIs (Temporal gRPC):** [`dependencies.md`](dependencies.md) —
  how to call it and generate the local, gitignored snapshot in `_api_/temporal/`
  (`scripts/temporal-api.sh refresh`).
  Read it before writing or changing the Temporal adapter in `workflow/`.
- API contract: [`../_specs_/api/rest-api.md`](../_specs_/api/rest-api.md) ·
  realtime: [`../_specs_/api/realtime.md`](../_specs_/api/realtime.md)
- Running the stack: [`../getting-started.md`](../getting-started.md)

## Setup / run / test

```bash
uv sync                                          # install deps
uv run uvicorn app.main:app --reload --port 8010 # API at /api/v1, docs at /api
uv sync --extra dev && uv run pytest             # tests
../start.sh                                      # whole stack (+ Temporal)
```

Local config: copy `.env.example` to `.env` (gitignored), read by `../start.sh`.

## Dependencies

Temporal is optional (the simulation engine runs in-process). Start it when a
task needs it, check it, and stop it when finished unless the user wants it
left running:

```bash
docker compose -f ../_infra_/docker-temporal/docker-compose.yml up -d
docker compose -f ../_infra_/docker-temporal/docker-compose.yml ps
scripts/temporal-api.sh call GetSystemInfo
docker compose -f ../_infra_/docker-temporal/docker-compose.yml down
```

## Structure (see README for the full tree)

```text
app/
  api/           HTTP boundary (routers, schemas, errors, WebSocket)
  application/   ControlCenter use-case facade (queries + commands)
  domain/        pure models/enums, snake_case → camelCase on the wire
  infra/         in-memory store + event bus, SQLite write-through, seed
  workflow/      port.py (engine contract) + simulation.py (MVP adapter)
tests/           one module per feature/area spec + test_constitution.py (layer checks)
```

## Conventions

- **Command-oriented API.** Expose business commands (Start, Approve, Retry…),
  never CRUD or engine internals.
- **Engine independence.** Temporal/engine concepts stay in `workflow/`;
  business code depends on `workflow/port.py` only.
- **Contract lockstep.** `domain/models.py` must match
  `frontend/src/types/domain.ts` (camelCase JSON).
- **Planning is immutable, Runtime is disposable, History is permanent.**
- **Cite the spec.** Code implementing a feature requirement carries
  `# spec NNN FR-N`; area-spec rules are cited by path
  (`# spec planning/schedules D5`).
- **Tests map to ACs.** One module per feature (`tests/test_<feature>.py`, module
  docstring names the spec); each AC test cites `# spec NNN AC-N` and ends its
  name with the id (`test_…_ac3`). Invariant tests end with the principle
  (`test_…_p4`). Tests stay offline: in-memory SQLite (`conftest.py`), injected
  clock, fake/in-process port — no Temporal, no network.
- **Layer boundaries are tested.** `tests/test_constitution.py` fails on a new
  engine import outside `workflow/` or a router reaching `infra/`/`workflow/`.
  Known deviations live in its allow-list *and* `../_specs_/clarification.md`.
- **Errors keep their cause** (P9): Problem+JSON `detail`, Timeline entries, and
  Schedule Run reasons state what actually failed; fallbacks say they fell back.

