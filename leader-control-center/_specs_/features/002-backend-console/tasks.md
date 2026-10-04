# Tasks: Backend Console (Gradio)

**Feature ID:** `002-backend-console` · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

- [x] T1 Add `gradio` to `backend/pyproject.toml`.
- [x] T2 `app/ui/client.py` — `ConsoleApi` + `ApiError` (FR-9, FR-10).
- [x] T3 `app/ui/render.py` — trees (FR-3..FR-6), detail views (FR-7), tables (FR-8), error view (FR-10).
- [x] T4 `app/ui/console.py` — sidebar + main area + JS bridge + deep link (FR-2, FR-6, FR-11, FR-12).
- [x] T5 Mount at `/ui` in `app/main.py`; `CONSOLE_UI_ENABLED` / `CONSOLE_API_BASE` in config (FR-1).
- [x] T6 Amend area specs (architecture, frontend) and the features index; backend README.
- [x] T7 `tests/test_backend_console.py` — AC-1..AC-10; run the backend suite.
