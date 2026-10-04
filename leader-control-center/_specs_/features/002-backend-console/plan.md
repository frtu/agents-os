# Implementation Plan: Backend Console (Gradio)

**Feature ID:** `002-backend-console` · **Spec:** [`spec.md`](spec.md)
**Status:** Draft
**Created:** 2026-10-04 · **Last Updated:** 2026-10-04

## Constitution Check

- [x] P1 Human first — read-only; Human Requests are shown, never answered here.
- [x] P2 Planning immutable — no writes at all.
- [x] P3 Command-oriented — only existing `/api/v1` queries; no new endpoints; no CRUD.
- [x] P4 Engine independence — the console sees only the API; a layer test forbids `app.workflow` imports (AC-8).
- [x] P5 Provider independence — n/a.
- [x] P6 Contract lockstep — no contract change; the console consumes the camelCase JSON as-is.
- [x] P7 Spec first — this spec + plan precede code; code cites `spec 002 FR-N`.
- [x] P8 Tested — `tests/test_backend_console.py`, one test per AC, offline (TestClient as the HTTP client).
- [x] P9 Error transparency — every failed read renders the read name, status and `detail` (FR-10).
- [x] P10 Simplest thing — server-rendered Gradio, HTML trees, no realtime; one new dependency.
- [x] P11 Ubiquitous language — UI labels mapped to glossary terms in the spec.

## Technical Context

- **Backend only.** New dependency: `gradio` (≥ 6), same as `leader-assistant`.
- No frontend change, no contract change.

## Architecture Overview

```text
app/ui/
  client.py   ConsoleApi — thin httpx wrapper over /api/v1; ApiError(read, status, detail)
  render.py   pure functions: JSON → sidebar HTML trees, detail Markdown, tables
  console.py  build_console() → gr.Blocks (sidebar + main area + JS click bridge)
app/main.py   create_app() mounts build_console() at /ui (FR-1)
```

- **Client (FR-9, FR-10).** `ConsoleApi(http: httpx.Client)`. Default client points
  at `http://127.0.0.1:{PORT}` (override `CONSOLE_API_BASE`). Non-2xx raises
  `ApiError` carrying the read label, status and Problem+JSON `detail`; transport
  failures raise `ApiError` with status `None` and the exception text. Tests pass a
  FastAPI `TestClient` (an `httpx.Client`) so everything stays in-process.
- **Refs.** Every entry carries a ref `kind:id` (`initiative:…`, `story:…`,
  `task:<storyId>/<taskId>`, `workflow:…`, `activity:…`, `schedule:…`,
  `execution:…`, `notification:…`, `attention:…`) or a group ref `group:<name>`.
  `open_ref(api, ref) → (title_md, body_md, raw_json)`; group refs return a table
  as Markdown.
- **Sidebar (FR-2..FR-6, FR-12).** `gr.Sidebar` with three `gr.Accordion`s, each
  one `gr.HTML` tree of `<details>` groups and `.entry[data-ref]` rows. A
  delegated JS listener (same bridge as `leader-assistant` sessions) stores the
  clicked ref, marks it `.active`, writes `?item=` via `history.replaceState`
  (FR-11), and clicks a hidden trigger whose `js` shim injects the ref into the
  Python handler.
- **Deep link (FR-11).** `demo.load` reads `request.query_params["item"]`.
- **Mount (FR-1).** `gr.mount_gradio_app(app, build_console(), path="/ui")`,
  after the API routers; disabled with `CONSOLE_UI_ENABLED=false`.

## Test Plan

`backend/tests/test_backend_console.py` (module docstring names spec 002):

| AC | Test | Level |
| -- | ---- | ----- |
| AC-1 | `test_console_mounted_at_ui_ac1` — `/ui/` 200 HTML; `/api` and `/api/v1/initiatives` unchanged | ASGI |
| AC-2 | `test_sidebar_menus_in_order_ac2` — Blocks config holds the three accordions in order + refresh | unit |
| AC-3 | `test_board_tree_lists_initiatives_stories_tasks_ac3` | unit over TestClient |
| AC-4 | `test_definitions_tree_lists_all_groups_ac4` | unit over TestClient |
| AC-5 | `test_executions_tree_lists_runtime_groups_ac5` | unit over TestClient |
| AC-6 | `test_open_each_kind_shows_summary_and_json_ac6` | unit over TestClient |
| AC-7 | `test_group_header_opens_table_ac7` | unit over TestClient |
| AC-8 | `test_console_uses_rest_api_only_ac8` | static (ast) |
| AC-9 | `test_failed_read_names_read_status_detail_ac9` | unit over TestClient + unreachable base |
| AC-10 | `test_deep_link_opens_entry_ac10` | unit |

Gate: `uv run pytest` green; frontend untouched.
