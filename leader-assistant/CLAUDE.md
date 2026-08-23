# CLAUDE.md — Leader Assistant

Guidance for Claude Code working in this repo. Read this first, then the spec kit.

## Workflow — spec-first (mandatory)

**Every request that modifies the application MUST start in `specs/` before any code
changes.** Specs are the source of truth (Constitution P11); code is downstream. The order
is non-negotiable:

1. **Spec first.** Add or update the relevant file(s) under `specs/` — the primary MOC
   (`specs/00`–`specs/21`) and/or the feature folder (`specs/NNN-*/spec.md`, and its
   `plan.md`/`tasks.md` when scope warrants). Capture the new/changed behaviour as numbered,
   testable **FR-N** requirements, **User Scenarios**, and **Acceptance Criteria**. If it
   touches a constitutional principle, amend `memory/constitution.md` (with a version bump)
   first.
2. **Then code.** Implement to satisfy the spec, citing the spec doc + requirement id in
   code comments (e.g. `spec 004 FR-25`).
3. **Then tests (always).** Every new feature or behavioural change MUST land with tests in
   the same change — a feature is not "done" until it is tested. Add/adjust tests that map
   back to the new ACs/FRs, and **link the spec id** each test covers in a comment or the
   test name (e.g. `# spec 004 FR-25` / `test_..._fr25`) so coverage is traceable to the
   spec. Run `uv run --extra dev pytest` and confirm it passes before considering the task
   complete.
4. **Keep them in sync.** Spec, code, and tests must agree at the end of the change; if
   implementation forces a design change, update the spec rather than letting it drift.

This applies to features, behavioural fixes, and API/endpoint changes alike. Pure
non-behavioural chores (formatting, comment typos, dependency bumps) may skip step 1. When
in doubt, write the spec.

## What this project is

A local, filesystem-only knowledge & specification assistant. All durable state is
Markdown + YAML in a git-versioned **workspace** — no database, no vector store
(Constitution P1/P10). A workspace holds three folders: `skills/` (installed skills),
`sessions/` (operational conversations), and `vault/` (the ingestion root — the durable
knowledge store, itself holding `raw/`, `wiki/`, `output/`). Interfaces call a single
**surface-agnostic capability layer** so REST and (future) chat stay in parity (P9).

Two distinct things live here, do not confuse them:

- **`specs/`** — the *build spec kit*: how to build the assistant. Static input.
- **A workspace's `vault/wiki/product/specs/`** — the *runtime spec kit* the finished
  assistant produces from its own knowledge. Not authored here.

> **Docs describe the target; code lags.** These docs (and the spec kit) describe the
> **target Workspace model**. The current **app code and tests are not yet migrated** and
> still use the old names: container dir `Vaults/`, env vars `LEADER_VAULT_ROOT` /
> `LEADER_VAULT_PATH` / `LEADER_DEFAULT_VAULT` (default `default`), request field `vault`,
> endpoints `/api/vaults`, models `VaultList` / `VaultInfo`, and a flat
> `raw/ wiki/ sessions/ output/` layout (no `vault/` nesting, no `skills/`). Where a
> runnable example below (curl smoke tests) uses the old names, that reflects the code as
> it ships today. Don't assume the code already matches the target.

## Spec kit (source of truth)

`specs/` follows the GitHub Spec-Kit standard (constitution → spec → plan → tasks):

- `memory/constitution.md` — 13 ratified principles; every plan is checked against it.
- `specs/00`–`specs/21` — the primary spec (numbered MOCs). `13-api.md` defines the API
  parity model; `03-vault.md` defines the workspace layout; `05-zettelkasten.md` the
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
(future chat)               ┘── app/capabilities.py ──▶ app/vault.py ──▶ workspace (git)
```

- `app/capabilities.py` is the **only** path from an interface to the workspace (P9). Add
  new behaviour here first, then expose it on the REST surface — never let `api.py`
  touch the filesystem directly.
- `app/vault.py` (module name unchanged — code not yet migrated) owns workspace
  resolution, scaffolding, the `vault/raw/` write-guard (P2), the append-only `log.md`,
  and per-workspace `git init`.
- Each workspace is its **own git repo**, isolated from any enclosing project repo.
  `_git_commit` refuses to commit if `git rev-parse --show-toplevel` != the workspace
  path — this prevents accidentally committing to a parent checkout.

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
| `GET`  | `/api/workspaces` | — | `WorkspaceList` (workspaces, root, default) |
| `POST` | `/api/workspaces` | `{name}` | `WorkspaceInfo` |
| `GET`  | `/api/workspaces/{selector}` | path selector | `WorkspaceInfo` |
| `POST` | `/api/ingest` | `{workspace?,title,content,provenance}` | `IngestReport` |
| `POST` | `/api/query` | `{workspace?,question}` | `Answer` (reply + citations) |
| `POST` | `/api/plan` | `{workspace?,request}` | `Plan` (risk, steps, requires_approval) |
| `GET`  | `/api/lint` | `?workspace=` | `LintReport` |
| `GET`  | `/api/spec` | `?path=&workspace=` | `{path, content}` |
| `POST` | `/api/chat` | `ChatRequest` | `ChatAnswer` |
| `POST` | `/api/chat/stream` | `ChatRequest` | SSE stream of `ChatDelta` |
| `GET`  | `/api/chat/status` | `?conversation_id=&workspace=` | `ChatStatus` (running, exists) |
| `GET`  | `/api/chat/interaction` | `?conversation_id=&workspace=` | pending `Interaction` or null (spec 008) |
| `POST` | `/api/chat/interaction` | `InteractionResponse` | `ChatAnswer` (resumes the task) |
| `POST` | `/api/chat/interaction/stream` | `InteractionResponse` | SSE stream of `ChatDelta` |

(Target contract; code still serves the `/api/vaults` + `vault` variants — see the
divergence note above.)

`ChatRequest`: `{message, workspace?, conversation_id?, approve=false}`.
`ChatAnswer`: `{workspace, conversation_id, reply, citations[], pending_plan?, executed}`.
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
├── vault.py        # resolver, scaffolder, vault/raw/ guard, log, per-workspace git
└── config.py       # env-based workspace resolution
specs/              # build spec kit (see above)
templates/          # externalized, human-owned output templates (reuse-before-create, P7)
memory/             # constitution + agent memory
```

Target runtime workspace layout (what the resolver/scaffolder should produce; code is not
yet migrated — see the divergence note):

```text
Workspaces/<workspace-name>/
├── skills/         # installed skills — each a file/folder or a reference-link to another folder
├── sessions/       # operational conversations (short-term memory)
└── vault/          # ingestion root — the durable knowledge store (P1)
    ├── raw/        # immutable, human-owned sources (never modified by the pipeline)
    ├── wiki/       # LLM workspace — all durable knowledge (portal.md, log.md, sources/, …)
    └── output/     # generated artifacts (reports, query results)
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
| `LEADER_WORKSPACE_ROOT` | root holding `Workspaces/<name>/` | `./Workspaces` |
| `LEADER_WORKSPACE_PATH` | explicit single-workspace path (wins over root) | — |
| `LEADER_DEFAULT_WORKSPACE` | default workspace selector | `_default_` |
| `LEADER_HOST` / `LEADER_PORT` | server bind | `127.0.0.1` / `8000` |

(Target names; code still reads `LEADER_VAULT_ROOT` / `LEADER_VAULT_PATH` /
`LEADER_DEFAULT_VAULT` with default `default` — see the divergence note above.)

Workspaces are git-ignored (`Workspaces/`, `.tmp-workspaces/`). The chat surface (`ask()`) uses the
`claude-agent-sdk` runtime, which needs the `claude` CLI / credentials to be reachable;
when it is not, `ask()` falls back to a deterministic cited answer via `query` so the
endpoint still works offline. All non-chat capabilities run without any credentials.

## Conventions & invariants (don't break these)

- **Internal writers never touch `vault/raw/`** — the ingestion pipeline/assistant MUST NOT
  write under `vault/raw/` (P2 v1.1.0); go through `vault.guard_write_path`, which rejects
  raw writes. `vault/raw/` is *human-owned*: humans may add/modify/delete raw sources, and the
  app does so on their behalf only via the sanctioned upload channel
  (`capabilities.deposit_raw`, feature 004).
- **`log.md` is append-only** — use `vault.append_log`, never edit existing lines.
- **Only the capability layer reaches the workspace** — keep `api.py` thin.
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
