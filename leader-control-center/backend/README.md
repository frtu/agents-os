# Leader Control Center — Backend

FastAPI service that exposes the human-in-the-loop control plane for durable AI
workflows. It serves a **command-oriented** REST API plus a WebSocket stream
under `/api/v1`, backed by a **SQLite** store (in-memory working set, write-through
to disk) and a background **simulation engine** that stands in for a real durable
engine (Temporal) during the MVP.

The backend implements the specs in [`../_specs_/`](../_specs_) and the condensed
design docs in [`../_docs_/`](../_docs_). If code and spec disagree, `_specs_/domain/`
wins, then the root [`../README.md`](../README.md).

**Persistence:** the datastore for the MVP is **SQLite**, a single file under the
project-root `data/` directory (`../data/` relative to `backend/`). The storage
technology and its deltas from the canonical Postgres data model are defined in
[`storage.md`](storage.md), which overlays
[`../_specs_/database/data-model.md`](../_specs_/database/data-model.md).

## Stack

- Python 3.11+ · FastAPI · Pydantic v2 · Uvicorn
- [uv](https://docs.astral.sh/uv/) for env + running
- [`temporalio`](https://github.com/temporalio/sdk-python) Python SDK for the Temporal adapter (see [`dependencies.md`](dependencies.md))
- **SQLite** file at `../data/leader-control-center.db` (see [`storage.md`](storage.md)):
  aggregates persist as JSON documents, written through on the event bus; state
  survives restarts and seeds only on first run

## Dependencies

External services are **optional** in the MVP (the simulation engine runs
in-process). Start them on demand when working on the adapter that needs them.

| Dependency | Location (relative to `backend/`) | Start | Stop | Endpoints |
| ---------- | --------------------------------- | ----- | ---- | --------- |
| Temporal (+ Postgres, UI) | [`../_infra_/docker-temporal`](../_infra_/docker-temporal) | `docker compose -f ../_infra_/docker-temporal/docker-compose.yml up -d` | `docker compose -f ../_infra_/docker-temporal/docker-compose.yml down` | gRPC `localhost:7233` (host port, `TEMPORAL_GRPC_PORT`) · UI `http://localhost:8080` · Postgres `localhost:5432` |

The compose file reads its image versions from the `.env` next to it; `-f`
resolves that `.env` from the compose file's folder, so it works from `backend/`.

From the project root, `./start.sh --temporal` (or `WITH_TEMPORAL=1 ./start.sh`)
starts Temporal with the backend and frontend, and stops it on Ctrl+C.

## Run

Whole stack (backend + frontend, optional Temporal) from the project root. It
runs `backend/start.sh` and `frontend/start.sh` side by side; Ctrl+C stops both,
and if either exits the other is stopped too:

```bash
./start.sh                                    # backend :8010 (+ Temporal), frontend :5173
./start.sh -p 8100 -f 5180                    # custom backend / frontend ports
./start.sh --no-temporal                      # skip Temporal
./start.sh --keep-temporal                    # leave Temporal up after Ctrl+C
./start.sh --help                             # all options
```

The three scripts share their helpers (`.env` loading, port checks, process
cleanup) through `../scripts/start-lib.sh`.

Backend + Temporal (no frontend), from `backend/`:

```bash
./start.sh                                    # Temporal (docker compose) + backend :8010
./start.sh -p 8100                            # custom backend port
./start.sh --keep-temporal                    # leave Temporal up after Ctrl+C
./start.sh --no-temporal                      # backend only, no Docker
./start.sh --help                             # all options
```

It loads `backend/.env`, refuses busy ports, and reuses a Temporal that is
already healthy, in which case it leaves it running on exit. Ctrl+C otherwise
stops the backend and the Temporal containers it started. Once Temporal is
healthy it refreshes the local `_api_/temporal` snapshot.

Backend only, by hand:

```bash
uv sync                                       # install deps
uv run uvicorn app.main:app --reload --port 8010
```

- API base: `http://localhost:8010/api/v1`
- WebSocket stream: `ws://localhost:8010/api/v1/stream`
- OpenAPI docs: `http://localhost:8010/api`

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
    activities.py    ActivityDefinitionService — CRUD, template render, webhook
                     test (bash is syntax-checked only, never run here)
    schedules.py     ScheduleService — Schedule commands + the process manager
                     that turns due occurrences into Stories (overlap, catch-up,
                     failure count, auto-archive)
    service.py       ControlCenter — the use-case facade the API calls.
                     Queries read store projections; commands validate intent
                     and delegate runtime effects to the engine. build_control_
                     center() composes store + engine + seed.

  domain/            pure business model (no I/O)
    activity_template.py  {{param}} rendering per slot (shell/URL/JSON) + ${env:NAME}
    models.py        Pydantic projections; serialize snake_case -> camelCase to
                     match frontend/src/types/domain.ts exactly
    enums.py         all status/type enums (the state-machine vocabulary)
    board.py         Kanban column derivation (column_for / empty_columns)
    decisions.py     which Decision actions each Human Request type allows
    events.py        realtime message bus types (MessageType, RealtimeMessage)

  infra/
    store.py         in-memory working set (aggregates + indexes) + event bus
    db.py            SQLite persistence (write-through on the bus); see storage.md
    seed.py          sample portfolio/initiatives/stories/tasks on first run

  workflow/
    port.py          WorkflowEngine Protocol (engine-agnostic contract)
    scheduler_port.py  SchedulerPort Protocol (time triggers)
    in_process_scheduler.py  default SchedulerPort adapter (SQLite cursor + tick)
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
| Activity definitions | `GET/POST /activity-definitions` · `GET/PATCH/DELETE /activity-definitions/{id}` | UI "Tasks": reusable bash / webhook building blocks (see [`_specs_/execution/activity-definitions.md`](../_specs_/execution/activity-definitions.md)) |
| | `POST /activity-definitions/{id}/render` · `/test` | preview with parameters; send a webhook once (secrets from `${env:NAME}`) |
| Schedules | `GET /schedules` · `GET /schedules/{id}` · `GET /schedules/{id}/runs` | time-triggered Stories (see [`_specs_/planning/schedules.md`](../_specs_/planning/schedules.md)) |
| | `POST /schedules/preview` · `POST /schedules` · `PATCH /schedules/{id}` | preview sentence + next occurrences, create, update |
| | `POST /schedules/{id}/pause` · `/resume` · `/trigger` · `/archive` | lifecycle commands; `trigger` = Run now |
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

[`.env.example`](.env.example) is the committed template. For local settings,
copy it to `.env`, which is gitignored, so your ports and paths are never committed:

```bash
cp .env.example .env                          # then edit .env
```

`./start.sh`, `../frontend/start.sh` and `../start.sh` load `backend/.env`. The app itself does not read `.env`: when
you run `uvicorn` directly, set variables inline instead, e.g.
`PORT=9000 uv run uvicorn app.main:app --reload --port 9000`.

Precedence in `start.sh`: CLI flags > shell environment > `backend/.env` > defaults.

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `HOST` | `0.0.0.0` | backend bind address (`start.sh -h`) |
| `PORT` | `8010` | backend port (`start.sh -p`); `start.sh` points the vite `/api` proxy at it |
| `FRONTEND_PORT` | `5173` | vite dev server port (`start.sh -f`) |
| `WITH_TEMPORAL` | `0` | `1` makes `start.sh` start and stop Temporal (see [Dependencies](#dependencies)) |
| `SQLITE_PATH` | `../data/leader-control-center.db` | SQLite file path (project-root `data/`); dir is created on startup |
| `SIMULATION_TICK_SECONDS` | `2.5` | seconds between simulation ticks; `0` disables |
| `SCHEDULER_TICK_SECONDS` | `5` | seconds between scheduler ticks (fire due Schedule occurrences, settle runs); `0` disables firing |
| `CORS_ORIGINS` | `http://localhost:$FRONTEND_PORT,http://127.0.0.1:$FRONTEND_PORT` | allowed origins; `start.sh` derives it from `FRONTEND_PORT` when unset |
