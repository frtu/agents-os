# CLAUDE.md — Leader Assistant

Guidance for Claude Code working in this repo. Read this first, then the spec kit.

## What this project is

A local, filesystem-only knowledge & specification assistant. All durable state is
Markdown + YAML in a git-versioned **vault** — no database, no vector store
(Constitution P1/P10). Interfaces call a single **surface-agnostic capability layer**
so REST and (future) chat stay in parity (P9).

Two distinct things live here, do not confuse them:

- **`specs/`** — the *build spec kit*: how to build the assistant. Static input.
- **A vault's `wiki/product/specs/`** — the *runtime spec kit* the finished assistant
  produces from its own knowledge. Not authored here.

## Spec kit (source of truth)

`specs/` follows the GitHub Spec-Kit standard (constitution → spec → plan → tasks):

- `memory/constitution.md` — 13 ratified principles; every plan is checked against it.
- `specs/00`–`specs/21` — the primary spec (numbered MOCs). `13-api.md` defines the API
  parity model; `03-vault.md` defines the vault layout; `05-zettelkasten.md` the
  concept lifecycle math.
- `specs/001-leader-assistant/plan.md` — the **decided** stack & architecture (this is
  what the code implements).
- `specs/001-leader-assistant/tasks.md` — the ordered build (T001…T095). Use it as the
  backlog; it maps each task to the spec/invariant it satisfies.
- `specs/README.md` — index + reading order.

When README and references conflict, references win (README §32). When touching a
behaviour, cite the spec doc it comes from in code comments (e.g. `spec 03-vault AC2`).

## Architecture

```text
REST (FastAPI, app/api.py) ─┐
(future chat)               ┘── app/capabilities.py ──▶ app/vault.py ──▶ vault (git)
```

- `app/capabilities.py` is the **only** path from an interface to the vault (P9). Add
  new behaviour here first, then expose it on the REST surface — never let `api.py`
  touch the filesystem directly.
- `app/vault.py` owns vault resolution, scaffolding, the `raw/` write-guard (P2), the
  append-only `log.md`, and per-vault `git init`.
- Each vault is its **own git repo**, isolated from any enclosing project repo.
  `_git_commit` refuses to commit if `git rev-parse --show-toplevel` != the vault path
  — this prevents accidentally committing to a parent checkout.

## API surface (endpoints)

Base URL `http://localhost:8000`. Every route is a thin call over `capabilities`;
consequential requests return a **plan** for approval rather than mutating (P8 / 13-api
AC2). The human web UI (Gradio, spec 003) owns `/`, so Swagger is relocated to **`/api`**
(`docs_url="/api"`) · ReDoc **`/redoc`** · OpenAPI **`/openapi.json`**.

| Method | Path | Body / params | Returns |
|--------|------|---------------|---------|
| `GET`  | `/` | — | Gradio web UI (spec 003) |
| `GET`  | `/api` | — | Swagger UI |
| `GET`  | `/health` | — | `{"status":"ok"}` |
| `GET`  | `/api/vaults` | — | `VaultList` (vaults, root, default) |
| `POST` | `/api/vaults` | `{name}` | `VaultInfo` |
| `GET`  | `/api/vaults/{selector}` | path selector | `VaultInfo` |
| `POST` | `/api/ingest` | `{vault?,title,content,provenance}` | `IngestReport` |
| `POST` | `/api/query` | `{vault?,question}` | `Answer` (reply + citations) |
| `POST` | `/api/plan` | `{vault?,request}` | `Plan` (risk, steps, requires_approval) |
| `GET`  | `/api/lint` | `?vault=` | `LintReport` |
| `GET`  | `/api/spec` | `?path=&vault=` | `{path, content}` |
| `POST` | `/api/chat` | `ChatRequest` | `ChatAnswer` |
| `POST` | `/api/chat/stream` | `ChatRequest` | SSE stream of `ChatDelta` |

`ChatRequest`: `{message, vault?, conversation_id?, approve=false}`.
`ChatAnswer`: `{vault, conversation_id, reply, citations[], pending_plan?, executed}`.
`ChatDelta` (SSE, one `data:` line each; final has `done=true`): same fields as
`ChatAnswer` plus `done`. Resend `conversation_id` to continue a thread; set
`approve=true` to execute a stored `pending_plan`. Shapes live in `app/models.py` and
render interactively at `/api` (Swagger).

## Project structure

```text
app/
├── __main__.py     # uvicorn launcher; prints the Swagger URL banner on startup
├── api.py          # FastAPI REST surface (Swagger at /api); mounts the Gradio UI at /
├── ui.py           # Gradio web UI (spec 003); calls /api/* over HTTP only (P9)
├── capabilities.py # surface-agnostic capability layer — the parity boundary (P9)
├── models.py       # pydantic request/response contracts (the Swagger schemas)
├── vault.py        # resolver, scaffolder, raw/ guard, log, per-vault git
└── config.py       # env-based vault resolution
specs/              # build spec kit (see above)
templates/          # externalized, human-owned output templates (reuse-before-create, P7)
memory/             # constitution + agent memory
```

## Commands

```bash
uv sync                          # install deps
uv run leader-assistant          # start server; banner prints Swagger URL
uv run python -m app             # same, module form
uv run --extra dev pytest        # run the API test suite (pytest is in the `dev` extra)
LEADER_LIVE_AGENT=1 uv run --extra dev pytest   # also run the opt-in live-agent test
```

Quick smoke test while the server runs (default port 8000):

```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/api/vaults -H 'content-type: application/json' -d '{"name":"demo"}'
curl -s -X POST localhost:8000/api/ingest -H 'content-type: application/json' \
  -d '{"vault":"demo","title":"Note","provenance":"notes","content":"hello"}'
curl -s -X POST localhost:8000/api/query  -H 'content-type: application/json' \
  -d '{"vault":"demo","question":"hello"}'
```

## Environment

| Var | Purpose | Default |
|-----|---------|---------|
| `LEADER_VAULT_ROOT` | root holding `Vaults/<name>/` | `./Vaults` |
| `LEADER_VAULT_PATH` | explicit single-vault path (wins over root) | — |
| `LEADER_DEFAULT_VAULT` | default vault selector | `default` |
| `LEADER_HOST` / `LEADER_PORT` | server bind | `127.0.0.1` / `8000` |

Vaults are git-ignored (`Vaults/`, `.tmp-vaults/`). The chat surface (`ask()`) uses the
`claude-agent-sdk` runtime, which needs the `claude` CLI / credentials to be reachable;
when it is not, `ask()` falls back to a deterministic cited answer via `query` so the
endpoint still works offline. All non-chat capabilities run without any credentials.

## Conventions & invariants (don't break these)

- **Never write under `raw/`** — it's immutable (P2). Go through `vault.guard_write_path`.
- **`log.md` is append-only** — use `vault.append_log`, never edit existing lines.
- **Only the capability layer reaches the vault** — keep `api.py` thin.
- **Consequential requests return a plan, not silent execution** (spec 13-api AC2). See
  `capabilities.plan`; `_CONSEQUENTIAL` classifies risky verbs.
- **Portal is updated on every ingest** (`_update_portal`).
- **No DB / vector store** as canonical storage (P1/P10). Markdown + YAML + git only.
- Keep new capabilities mirrored 1:1 across REST and chat (P9 parity; parity test is
  task T093 / feature 002 AC-7).
- **Chat is a surface over `capabilities.ask()`** — the agent's tools ARE the capability
  functions (`query`/`spec_read`/`plan`); it has no raw filesystem browse or write tool
  (feature 002 D3). Conversations persist one-file-per-thread under `sessions/` and resume
  by id after a restart (`app/conversation.py`).

## Current status

Implemented (MVP subset of `tasks.md`): vault resolve/scaffold + `raw/` guard, per-vault
git, ingest → source summary + portal + log, cited `query`, plan-first `plan`, `lint`,
`spec_read`, and the FastAPI surface with Swagger. **Feature 002 chat**: `ask()` /
`ask_stream()` over the agent runtime, durable/resumable `sessions/` conversation store,
plan-first consequential gating with approve-to-execute, `POST /api/chat` +
`POST /api/chat/stream` (SSE), Product Owner persona (`app/persona.py`).

**Tests**: `tests/` drives the FastAPI app over HTTP (`TestClient`), one test per user
story — `test_rest_api.py` (feature 001) and `test_chat_api.py` (feature 002 AC-1..AC-10).
Runs offline & deterministic (the `offline_agent` fixture forces chat's no-LLM fallback);
each test uses a throwaway vault under a tmp dir. Run with `uv run --extra dev pytest`;
add `LEADER_LIVE_AGENT=1` to also exercise the opt-in live-agent test.

Not yet: dreaming, risk-branching, continuous spec generation, and output/template reuse.
