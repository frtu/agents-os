# Tasks: Assistant Web UI

**Feature ID:** `003-assistant-ui` · **Plan:** [`plan.md`](plan.md)
**Last Updated:** 2026-08-16

> Ordered build steps derived from [`spec.md`](spec.md) and [`plan.md`](plan.md). Each
> references the FR/AC or invariant it satisfies. `[P]` = parallelizable (no shared files,
> no dependency). Consumes feature 002 chat endpoints and feature 001 workspace endpoints; adds
> **no** capability (P9).

## Legend

- `[ ]` pending · `[x]` done · `[P]` parallelizable
- Refs: `FR-n`/`AC-n` from [`spec.md`](spec.md); `[[NN-name]]` primary specs; `Pn` constitution.

## Setup

- [ ] T001 Add `gradio` and `httpx` to `pyproject.toml` dependencies; `uv sync`; add a tiny
  smoke import test. (plan Technical Context)

## Docs relocation & UI mount (server wiring)

- [ ] T010 In `app/api.py`, set FastAPI `docs_url="/api"` (Swagger UI at `/api/`) and remove
  the `@app.get("/")` → `/docs` redirect so `/` is free for the UI. (FR-2, D4)
- [ ] T011 Decide + apply placement of `openapi.json` / ReDoc (keep at `/openapi.json`,
  `/redoc`, or move under `/api/`); document the choice. (FR-2; plan Open Questions)
- [ ] T012 Mount the Gradio UI on the FastAPI app at `/` via
  `gr.mount_gradio_app(app, build_demo(), path="/")`. (FR-1, D1)
- [ ] T013 [P] Update the startup banner in `app/__main__.py`: `UI : {base}/`,
  `Swagger : {base}/api/`. (FR-1, FR-2)

## UI — API client (UI → REST, same origin)

- [ ] T020 `app/ui.py` API client helpers over HTTP only: `list_workspaces()` / `create_workspace(name)`
  (`/api/workspaces`), `chat(...)` (`/api/chat`), `stream_chat(...)` (`/api/chat/stream`, SSE).
  No import of `app.capabilities`/`app.vault`. (FR-3, FR-4, FR-6, FR-10; P9; D3)
- [ ] T021 SSE consumption: read `text/event-stream` from `/api/chat/stream` incrementally,
  yielding accumulated `reply` + `conversation_id` (+ `citations`/`pending_plan`); fall back
  to `/api/chat` when streaming is unavailable. (FR-4)
- [ ] T022 Error mapping: turn non-2xx API responses (e.g. missing named workspace) into a
  visible UI message. (FR-11; AC-9)

## UI — chat surface (startup)

- [ ] T030 `build_demo()` Gradio `gr.Blocks`: title, `gr.Chatbot`, input textbox, and
  `gr.State` for `conversation_id` and active workspace. (FR-1)
- [ ] T031 Chat handler streams the reply via `stream_chat(...)` and renders it incrementally.
  (FR-4)
- [ ] T032 Conversation continuity: capture the returned `conversation_id` into state and
  resend it on the next turn. (FR-5)
- [ ] T033 [P] Render `citations` returned with an answer. (FR-9; P6)

## UI — workspace picker

- [ ] T040 Workspace dropdown populated from `GET /api/workspaces`; selecting sets the active
  workspace in state; show the active workspace to the user. (FR-6, FR-7)
- [ ] T041 "Create workspace" control → `POST /api/workspaces` on explicit user action, then refresh
  the dropdown so the new workspace appears. (FR-6; D2)
- [ ] T042 Default-workspace behavior when none selected (send `workspace: null`; server defaults). (FR-7; P13)

## UI — plan-first approval (P8)

- [ ] T050 Pending-plan panel: when a reply carries `pending_plan`, render the plan steps and
  risk. (FR-8; [[09-planning]])
- [ ] T051 Approval control: on explicit user activation, resend the same turn with
  `approve: true` (same `conversation_id`); no auto-approval. (FR-8; P8; feature 002 D2)

## Validation (map to AC)

- [ ] T060 AC-1: `GET /` returns the chat UI (startup surface). (FR-1)
- [ ] T061 AC-2: Swagger UI resolves at `/api/` **and** `/api/chat` + `/api/workspaces` still
  resolve (no route conflict). (FR-2)
- [ ] T062 AC-3: a UI message renders incrementally (stream), and matches the non-streaming
  reply content. (FR-4)
- [ ] T063 AC-4: a follow-up reuses the returned `conversation_id` and is context-aware. (FR-5)
- [ ] T064 AC-5: picker lists workspaces, switching works, a UI-created workspace appears; none
  selected → default workspace used. (FR-6, FR-7)
- [ ] T065 AC-6: consequential request shows a plan + approval control; no mutation until
  approval; approval resends `approve: true` and executes. (FR-8; P8)
- [ ] T066 AC-7: citations are displayed when returned. (FR-9)
- [ ] T067 AC-8: `app/ui.py` imports no `app.capabilities`/`app.vault` and touches no workspace
  file directly — verified by inspection/test (UI calls only `/api/*`). (FR-3, FR-10; P9)
- [ ] T068 AC-9: an API error (e.g. missing named workspace) is shown in the UI, not swallowed. (FR-11)

## Dependencies

- T001 precedes everything (deps installed).
- T010 (docs relocation) + T012 (UI mount) precede T060/T061.
- T020 precedes T021, T022, and all UI handlers (T031, T040, T041, T050, T051).
- T021 precedes T031/T062; T030 precedes T031–T033, T040–T042, T050–T051.
- T050 precedes T051 (a plan must be shown before it can be approved).

## Resolved decisions (from spec.md)

- **D1** — Gradio UI mounted on the existing FastAPI server at `/` (one process/port). (T012)
- **D2** — scope is chat + workspace picker only; full capability console deferred. (T030–T051)
- **D3** — the UI calls the backend over the HTTP REST API, not the in-process capability
  layer; verified by AC-8. (T020, T067)
- **D4** — Swagger relocates to `/api/`; `/` serves the UI; REST keeps `/api/<resource>`. (T010)
