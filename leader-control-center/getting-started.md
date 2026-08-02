# Getting Started

Leader Control Center is a human-in-the-loop control plane for durable AI
workflows. It has two parts:

- **Frontend** — React + Vite console (`frontend/`). Ships with an in-browser
  mock backend, so it runs with or without the API.
- **Backend** — FastAPI + an in-memory store and a background simulation engine
  (`backend/`). Serves the REST API and a WebSocket stream under `/api/v1`.

## Prerequisites

| Tool                             | Version | Used for                         |
| -------------------------------- | ------- | -------------------------------- |
| [uv](https://docs.astral.sh/uv/) | latest  | Python env + running the backend |
| Python                           | 3.11+   | backend runtime (managed by uv)  |
| Node.js                          | 18+     | frontend build/dev server        |
| npm                              | 9+      | frontend dependencies            |

## Choose how to run

- **Mock only (fastest)** — frontend against the in-browser mock backend. No
  Python needed. Good for UI work.
- **Full stack** — real FastAPI backend + frontend. Needed to exercise the REST
  API, WebSocket realtime, and the background simulation.

> The checked-in `frontend/.env.local` sets `VITE_USE_MOCKS=false`, so a fresh
> checkout expects a running backend. For mock-only, set `VITE_USE_MOCKS=true`
> (see below).

---

## Option A — Mock only

```bash
cd frontend
npm install
echo "VITE_USE_MOCKS=true" > .env.local   # override the checked-in default
npm run dev                               # http://localhost:5173
```

The mock seeds sample initiatives and a sample workflow definition, and emits
simulated realtime events, so the Board, Workflow, and Attention Queue update
live without a backend.

---

## Option B — Full stack

Run the backend and frontend in two terminals.

### 1. Backend

```bash
cd backend
uv sync                                   # install dependencies
uv run uvicorn app.main:app --reload --port 8000
```

- API base: `http://localhost:8000/api/v1`
- WebSocket stream: `ws://localhost:8000/api/v1/stream`
- Interactive docs (OpenAPI): `http://localhost:8000/docs`

A background simulation advances running executions every ~2.5s (raising human
requests, producing artifacts, emitting realtime events).

### 2. Frontend

```bash
cd frontend
npm install
# .env.local already sets VITE_USE_MOCKS=false to use the real backend
npm run dev                               # http://localhost:5173
```

Vite proxies `/api` (REST + WebSocket) to `http://localhost:8000`, so no CORS
setup is needed in dev. Open `http://localhost:5173`.

---

## Configuration

### Backend (`backend/.env.example`)

| Variable                  | Default                                       | Purpose                                           |
| ------------------------- | --------------------------------------------- | ------------------------------------------------- |
| `HOST`                    | `0.0.0.0`                                     | bind address                                      |
| `PORT`                    | `8000`                                        | bind port (vite proxy targets `:8000`)            |
| `SIMULATION_TICK_SECONDS` | `2.5`                                         | seconds between simulation ticks; `0` disables it |
| `CORS_ORIGINS`            | `http://localhost:5173,http://127.0.0.1:5173` | comma-separated allowed origins                   |

Copy `backend/.env.example` to `backend/.env` to customize. Environment
variables also work inline: `PORT=9000 uv run uvicorn app.main:app --reload`.

### Frontend (`frontend/.env.example`)

| Variable            | Default          | Purpose                                          |
| ------------------- | ---------------- | ------------------------------------------------ |
| `VITE_USE_MOCKS`    | `true`           | `true` = in-browser mock; `false` = real backend |
| `VITE_API_BASE_URL` | `/api/v1`        | REST base (proxied in dev)                       |
| `VITE_WS_URL`       | `/api/v1/stream` | WebSocket URL (proxied in dev)                   |

Vite reads `.env.local` (git-ignored) over `.env`. Restart `npm run dev` after
changing env values.

---

## Verify it works

Backend, from `backend/`:

```bash
uv sync --extra dev
uv run pytest                             # smoke tests
curl http://localhost:8000/api/v1/initiatives           # board projection
curl http://localhost:8000/api/v1/attention             # open decisions-to-make
curl http://localhost:8000/api/v1/workflow-definitions   # workflow blueprints
```

Frontend, from `frontend/`:

```bash
npm run typecheck                         # tsc --noEmit
npm run build                             # typecheck + production build
```

In the browser at `http://localhost:5173` you should see the Initiative board,
the Workflow page for authoring workflow definitions, the Attention Queue with
actionable decisions, and the notifications tray in the top bar.

Workflow definitions are reusable blueprints (a name, an input JSON Schema, and a
DSL definition string). Attach one to an initiative when creating it, then use
the "Use template" checkbox in the New Story sheet to render the definition's
input schema as a form.

---

## Common tasks

| Command                                | Where       | What                         |
| -------------------------------------- | ----------- | ---------------------------- |
| `uv run uvicorn app.main:app --reload` | `backend/`  | run API with hot reload      |
| `uv run pytest`                        | `backend/`  | run tests                    |
| `npm run dev`                          | `frontend/` | dev server (HMR)             |
| `npm run build`                        | `frontend/` | typecheck + production build |
| `npm run preview`                      | `frontend/` | serve the production build   |

---

## Troubleshooting

- **Frontend loads but no data / network errors** — `VITE_USE_MOCKS=false` but
  the backend isn't running. Start the backend (Option B) or switch to mocks
  (`VITE_USE_MOCKS=true`) and restart `npm run dev`.
- **CORS errors** — you're hitting the API cross-origin instead of via the vite
  proxy. Use `http://localhost:5173` (dev proxy), or add your origin to
  `CORS_ORIGINS`.
- **Port already in use** — change the backend `PORT` (and the vite proxy target
  in `frontend/vite.config.ts`) or the frontend `server.port`.
- **Env change had no effect** — Vite only reads env at startup; restart the dev
  server.
- **Data resets on restart** — expected. The backend store is in-memory and
  re-seeds on each start.
