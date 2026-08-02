# Leader Control Center — Backend

FastAPI service that exposes the human-in-the-loop control plane for durable AI
workflows. It serves a **command-oriented** REST API plus a WebSocket stream
under `/api/v1`, backed by an in-memory store and a background **simulation
engine** that stands in for a real durable engine (Temporal) during the MVP.

The backend implements the specs in [`../_specs_/`](../_specs_) and the condensed
design docs in [`../_docs_/`](../_docs_). If code and spec disagree, `_specs_/domain/`
wins, then the root [`../README.md`](../README.md).

## Stack

- Python 3.11+ · FastAPI · Pydantic v2 · Uvicorn
- [uv](https://docs.astral.sh/uv/) for env + running
- No database in the MVP — state is in-memory and re-seeds on every start

## Run

```bash
uv sync                                       # install deps
uv run uvicorn app.main:app --reload --port 8000
```

- API base: `http://localhost:8000/api/v1`
- WebSocket stream: `ws://localhost:8000/api/v1/stream`
- OpenAPI docs: `http://localhost:8000/docs`

A background loop ticks every `SIMULATION_TICK_SECONDS` (default 2.5s), advancing
running executions: raising Human Requests, producing Artifacts, appending
Timeline events, and emitting realtime messages. Set the interval to `0` to
disable it (see [`.env.example`](.env.example)).

## Test

```bash
uv sync --extra dev
uv run pytest
```

## Architecture

Layered, dependency arrows point inward. The domain has no FastAPI/HTTP imports;
business logic depends only on the `WorkflowEngine` port, so a Temporal adapter
can replace the simulation engine behind the same interface later.

```text
app/
  main.py            FastAPI factory: mounts routers under /api/v1, runs the
                     simulation tick as a lifespan background task
  config.py          env-driven Settings (HOST, PORT, tick seconds, CORS)

  api/               HTTP boundary (only layer that knows about FastAPI)
    routers/         one module per resource family (see Endpoints below)
    schemas.py       request bodies (responses reuse domain models directly)
    deps.py          DI: resolves the singleton ControlCenter
    errors.py        maps domain errors -> HTTP (NotFound 404, Invariant 422)
    ws.py            /stream WebSocket: broadcasts realtime bus messages

  application/
    service.py       ControlCenter — the use-case facade the API calls.
                     Queries read store projections; commands validate intent
                     and delegate runtime effects to the engine. build_control_
                     center() composes store + engine + seed.

  domain/            pure business model (no I/O)
    models.py        Pydantic projections; serialize snake_case -> camelCase to
                     match frontend/src/types/domain.ts exactly
    enums.py         all status/type enums (the state-machine vocabulary)
    board.py         Kanban column derivation (column_for / empty_columns)
    decisions.py     which Decision actions each Human Request type allows
    events.py        realtime message bus types (MessageType, RealtimeMessage)

  infra/
    store.py         in-memory aggregates + indexes + realtime event bus
    seed.py          sample portfolio/initiatives/stories/tasks on startup

  workflow/
    port.py          WorkflowEngine Protocol (engine-agnostic contract)
    simulation.py    SimulationEngine — MVP adapter; all runtime state
                     transitions live here (Temporal adapter slots in later)

tests/
  test_smoke.py      API smoke tests (httpx against the app)
```

### Request flow

```text
HTTP request → router (api/) → ControlCenter (application/) → domain / store
                                        │
                                        └── commands → WorkflowEngine port → SimulationEngine
                                                                                   │
                                        realtime bus ◄── store ◄── state changes ──┘
                                        │
                              WebSocket /stream broadcasts → frontend invalidates queries
```

## Endpoints (`/api/v1`)

The API exposes **business commands**, not CRUD. All paths are prefixed with
`/api/v1`.

| Area | Method + path | Purpose |
| ---- | ------------- | ------- |
| Board | `GET /initiatives` | initiative summary rows |
| | `POST /initiatives` | create initiative |
| | `POST /initiatives/reorder` | reorder initiatives |
| | `GET /initiatives/{id}/board` | full Kanban projection |
| Stories | `POST /stories` | create story |
| | `POST /stories/draft` | LLM-assisted draft prefill (heuristic in MVP) |
| | `GET /stories/{id}/tasks` | tasks for a story |
| | `GET /stories/{id}/artifacts` | artifacts for a story |
| | `POST /stories/{id}/start` | start a Story Execution |
| Tasks | `POST /tasks/{id}/ready` | mark task Ready |
| | `POST /tasks/{id}/start` | start a single Task Execution |
| Executions | `GET /executions/{id}` | execution detail |
| | `GET /executions/{id}/timeline` | append-only event history |
| | `POST /executions/{id}/cancel` · `/retry` | runtime commands |
| | `GET /executions/{id}/decisions` | open decisions-to-make |
| | `GET /executions/{id}/decisions/history` | immutable decision audit trail |
| | `POST /executions/{id}/decisions/{decisionId}/{action}` | resolve a request — `approve`, `reject`, `clarify`, `continue`, `abort`, `retry`, `select`, `custom` |
| Attention | `GET /attention` | global open Human Requests |
| Artifacts | `GET /artifacts/{id}` | artifact (with content) |
| Catalog | `GET /capabilities` · `GET /providers` | capability/provider catalog |
| Notifications | `GET /notifications` | open notifications |
| | `POST /notifications/{id}/open` · `/ack` · `/close` | lifecycle: UNREAD→READ→ACKED→CLOSED |
| Realtime | `WS /stream` | broadcast bus (client invalidates queries on messages) |

## Conventions

- **Planning is immutable, Runtime is disposable, History is permanent.** Runtime
  code never mutates planning objects.
- **Camel on the wire.** Domain models use snake_case in Python and serialize to
  camelCase; the JSON contract must stay in lockstep with
  `frontend/src/types/domain.ts`.
- **Engine independence.** Never reference Temporal/workflow concepts outside
  `workflow/`. Business code depends on `workflow/port.py` only.
- **Every pause is a Human Request; every Human Request yields one Decision.**

## Configuration

See [`.env.example`](.env.example). Copy to `.env` to customize, or set inline:
`PORT=9000 uv run uvicorn app.main:app --reload`.

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `HOST` | `0.0.0.0` | bind address |
| `PORT` | `8000` | bind port (vite proxy targets `:8000`) |
| `SIMULATION_TICK_SECONDS` | `2.5` | seconds between simulation ticks; `0` disables |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | allowed origins |
