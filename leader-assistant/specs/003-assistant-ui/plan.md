# Implementation Plan: Assistant Web UI

**Feature ID:** `003-assistant-ui` · **Spec:** [`spec.md`](spec.md)
**Status:** Draft
**Created:** 2026-08-16 · **Last Updated:** 2026-08-16

> Describes **how**. Turns [`spec.md`](spec.md) into architecture over the existing FastAPI
> REST surface (`app/api.py`) and the feature 002 chat endpoints. Requirements are
> referenced (FR-n, AC-n), not restated. Route paths below are binding where the spec fixes
> them (`/` = UI, `/api/` = Swagger), illustrative otherwise.

## Constitution Check

- [x] **P1 Vault is source of truth** — the UI holds only transient view state
  (`conversation_id`, active workspace); the durable conversation lives in `sessions/` on the
  workspace. ([[03-vault]], [[06-conversations]])
- [x] **P2 `vault/raw/` immutable** — the UI issues no writes except through API calls that
  already route through `vault.guard_write_path`. ([[18-security]])
- [x] **P3 Pipeline direction** — unaffected; the UI triggers nothing that writes to `vault/wiki/`
  outside the existing governed paths.
- [x] **P4 Zettelkasten discipline** — unaffected; the UI creates no concepts directly.
- [x] **P5 Concept lifecycle** — unaffected.
- [x] **P6 Traceability** — the UI displays the `citations` the API returns; `log.md` stays
  append-only on the server. ([[17-observability]])
- [x] **P7 Reuse before create** — reuses the archived `__OLD__/` Gradio pattern and the
  existing REST endpoints; no new capability or data path.
- [x] **P8 Human-in-the-loop** — a `pending_plan` is rendered with an explicit approval
  control; execution only on the user's approval turn (`approve: true`). ([[09-planning]])
- [x] **P9 Interface parity** — the UI is a **surface over the REST API**; it adds no
  capability and reaches the workspace only via `/api/*`. ([[12-assistant]], [[13-api]], [[14-chat]])
- [x] **P10 Portability** — no vector store, no new datastore; the UI is stateless beyond
  view state. ([[19-non-functional]])
- [x] **P11 Continuous specification generation** — untouched; the UI can *request* drafts
  only through existing API capabilities.
- [x] **P12 Risk-governed mutations** — consequential classification stays server-side in the
  capability layer; the UI just surfaces the resulting plan. ([[10-risk-engine]])
- [x] **P13 Multi-workspace** — a workspace picker selects the active workspace; default when none chosen.
  ([[03-vault]])

## Technical Context

- **Language / runtime:** Python 3.13+ (matches `app/`).
- **UI framework:** `gradio` — `gr.Blocks` for the chat + workspace-picker layout, mounted onto
  the existing FastAPI app via `gr.mount_gradio_app(app, demo, path="/")` (D1). This revives
  the archived `__OLD__/app.py` structure, but the UI **calls the REST API** instead of the
  in-process agent (D3).
- **API client (UI → API):** an HTTP client (e.g. `httpx.AsyncClient`) issuing same-origin
  calls to `/api/chat/stream` (SSE), `/api/chat`, and `/api/workspaces`. Streaming is consumed
  by reading `text/event-stream` chunks and yielding accumulated `reply` to the chatbot.
  *(SSE-consumption mechanism is the one deferred detail — see Open Questions.)*
- **Docs relocation:** configure FastAPI with `docs_url="/api"` so Swagger UI serves at
  `/api/`; remove the current `@app.get("/")` → `/docs` redirect (root now serves the UI).
  REST routes keep their `/api/<resource>` paths — FastAPI matches routes exactly, so `/api`
  (Swagger) does not shadow `/api/workspaces` etc. (FR-2). Decide alongside whether `openapi.json`
  and ReDoc move under `/api/` (Open Questions).
- **Server:** unchanged launcher (`app/__main__.py` / `uv run leader-assistant`); the mounted
  app is still `app.api:app`, one process/port. Update the startup banner to advertise the UI
  at `/` and Swagger at `/api/`.
- **Dependencies added:** `gradio` (UI) and `httpx` (UI→API client) in `pyproject.toml`.
- **Dependencies on other features:** consumes feature 002 endpoints (`/api/chat`,
  `/api/chat/stream`) and feature 001 workspace endpoints (`/api/workspaces`). Adds no capability.

> Rationale: the REST API already exists and is the parity boundary (P9). Mounting a Gradio
> UI that *calls that API* adds a human surface without a second data path, and continuously
> exercises the API the same way an external client would (D3).

## Architecture Overview

```text
Browser
  │  GET /            ──────────────► Gradio UI (startup surface, mounted on FastAPI)
  │  GET /api/        ──────────────► Swagger UI (docs_url="/api")
  ▼
Gradio UI process ──HTTP(same origin)──► /api/workspaces    (list / create)
  (app/ui.py)                            /api/chat           (full reply)
                                         /api/chat/stream    (SSE, incremental)
                                              │
                                              ▼
                                   app/capabilities.ask()  ──► agent ──► app/vault ──► workspace
                                   (feature 002 — unchanged)
```

- The UI is thin: capture input + view state (`conversation_id`, active workspace) → call the
  API → render reply, citations, and any `pending_plan`.
- Nothing in the UI touches `app/capabilities`, `app/vault`, or the filesystem — only HTTP
  (D3, FR-3, AC-8).
- Consequential turns stop at a `pending_plan`; the UI shows it and only on the user's
  approval resends with `approve: true` (P8, FR-8).

## Components

- **`app/ui.py` — Gradio UI builder.** `build_demo()` returns a `gr.Blocks` app with: a
  title, a workspace picker (dropdown from `GET /api/workspaces` + a "create workspace" control
  calling `POST /api/workspaces`), a `gr.Chatbot`, an input textbox, and `gr.State` for
  `conversation_id` and active workspace. Handlers call the API client and stream replies. Also
  exposes a
  pending-plan panel + approval control. (FR-1, FR-4, FR-5, FR-6, FR-8, FR-9)
- **API client helpers (in `app/ui.py`).** `stream_chat(workspace, message, conversation_id,
  approve)` consumes `/api/chat/stream` and yields accumulated reply + `conversation_id`
  (+ `pending_plan`/`citations`); `chat(...)` for the non-streaming fallback; `list_workspaces()`
  / `create_workspace(name)` over `/api/workspaces`. All same-origin HTTP (D3). (FR-3, FR-4, FR-6, FR-11)
- **`app/api.py` changes.** Set `docs_url="/api"` (Swagger relocation), remove the root
  redirect, and `gr.mount_gradio_app(app, build_demo(), path="/")` so `/` serves the UI.
  Keep all existing `/api/<resource>` routes. (FR-1, FR-2, D4)
- **`app/__main__.py` changes.** Update the startup banner: `UI : {base}/`,
  `Swagger : {base}/api/`. (FR-1, FR-2)
- **`pyproject.toml` changes.** Add `gradio` and `httpx` dependencies. (Technical Context)

## Data & File Contracts

The UI introduces **no new persisted contract**; it consumes the feature 002 chat contract
and the feature 001 workspace contract.

- **Chat call (UI → API):** `POST /api/chat/stream` (SSE) or `POST /api/chat` with
  ```json
  { "message": "string", "workspace": "active-or-null",
    "conversation_id": "held-by-ui-or-null", "approve": false }
  ```
  The UI stores `conversation_id` from the first response and resends it (FR-5). It sets
  `approve: true` only when the user activates the approval control on a shown plan (FR-8).
- **Chat response consumed:** `reply`, `conversation_id`, `citations[]`, `pending_plan`,
  `executed` (from `models.ChatAnswer` / `ChatDelta`). The UI renders `reply` (streamed),
  lists `citations`, and, when `pending_plan` is present, shows the plan + approval control.
- **Workspace calls (UI → API):** `GET /api/workspaces` → `{root, workspaces[], default}`
  populates the picker; `POST /api/workspaces {name}` creates a workspace on explicit user action
  (FR-6).
- **UI view state (transient, non-persisted):** `conversation_id` and active workspace in
  `gr.State`; the durable record remains `sessions/<id>.md` on the workspace (P1).

## Interfaces / Contracts

- **Browser routes (binding where fixed by spec):**
  - `GET /` → Gradio UI (startup surface). (FR-1)
  - `GET /api/` → Swagger UI (`docs_url="/api"`). (FR-2)
  - `GET/POST /api/<resource>` → existing REST endpoints, unchanged. (FR-2)
- **No new capability-layer functions** — parity is preserved by *not* adding any (P9);
  the UI is strictly a consumer of the existing REST surface (AC-8).

## Alternatives Considered

- **Static SPA / server-rendered HTML at `/`** — cleaner separation but more work and a new
  toolchain; **rejected** for this feature in favor of reviving the proven Gradio pattern
  (D1). Could be revisited if the UI outgrows Gradio.
- **UI calling the in-process capability layer directly** (no HTTP hop) — simpler wiring but
  **rejected** (D3): calling over HTTP keeps the UI a pure presentation surface, dogfoods the
  API, and keeps the parity boundary honest (P9).
- **Second process/port for the UI** — **rejected**: the spec requires one local service;
  mounting on the same FastAPI app keeps one process/port (FR-10).
- **Full capability console now** — **rejected** for scope (D2); deferred to a follow-up.
- **Keeping Swagger at `/docs` and putting the UI elsewhere** — **rejected**: the spec fixes
  `/` = UI and `/api/` = Swagger (D4, FR-1/FR-2).

## Risks & Mitigations

- **Route conflict `/api/` (docs) vs `/api/<resource>` (endpoints)** → FastAPI matches routes
  exactly; verify with a test that both Swagger and each endpoint resolve (AC-2).
- **SSE consumption inside the UI process** → use an async HTTP client that reads
  `text/event-stream` incrementally; if streaming proves brittle, fall back to `/api/chat`
  (FR-4). This is the one deferred implementation detail (Open Questions).
- **UI accidentally importing the capability layer** (breaking D3/P9) → enforce by an
  inspection/test that `app/ui.py` imports no `app.capabilities`/`app.vault` (AC-8).
- **Approval correlation** → the UI simply resends the same `conversation_id` with
  `approve: true`; the server correlates to the stored `pending-plan` (feature 002 D2), so no
  new correlation logic lives in the UI (FR-8).
- **Gradio theming/startup quirks** → the archived `__OLD__/style.py` (light-theme forcing,
  autofocus) is available to reuse (P7) if needed.
- **Backend errors surfaced poorly** → map non-2xx API responses to a visible UI message
  (FR-11, AC-9).

## Rollout / Sequencing

- **MVP:** relocate Swagger to `/api/` and mount a Gradio chat UI at `/`; single message →
  streamed reply via `/api/chat/stream`; conversation continuity via held `conversation_id`;
  default-workspace chat. Update the startup banner.
- **Then:** workspace picker (list/select via `/api/workspaces`, create on explicit action); citations
  display; `pending_plan` panel + explicit approval resending `approve: true`.
- **Later (out of this feature):** full capability console (ingest, lint, query, spec-read,
  outputs); richer conversation history browser; optional non-Gradio frontend.
