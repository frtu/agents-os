# Leader Control Center — Frontend

Supervision-first console for durable AI workflows. Implements the
[frontend spec](../specs/frontend/frontend.md): an **Initiative Kanban**, Story /
Task detail, an **Attention Queue**, Notifications, and an Artifact viewer.

## Stack

- React + TypeScript + Vite
- Tailwind CSS + shadcn/ui-style primitives
- TanStack Query (server state) + Zustand (UI state)
- WebSocket realtime layer ([realtime spec](../_specs_/api/realtime.md))

The UI issues **business commands** (Start, Approve, Retry…) rather than CRUD,
mirroring the [REST API spec](../_specs_/api/rest-api.md), and never surfaces
workflow-engine internals.

## Run

```bash
npm install
npm run dev      # http://localhost:5173
```

By default the app runs against an **in-browser mock backend**
(`VITE_USE_MOCKS=true`) so it is fully usable before the FastAPI backend exists.
The mock also emits simulated realtime events (executions progressing, human
requests appearing) so the Board and Attention Queue update live.

To point at a real backend, copy `.env.example` to `.env`, set
`VITE_USE_MOCKS=false`, and adjust `VITE_API_BASE_URL` / `VITE_WS_URL`.

## Scripts

- `npm run dev` — dev server
- `npm run build` — typecheck + production build
- `npm run typecheck` — `tsc --noEmit`
- `npm run preview` — preview the production build

## Structure

```
src/
  types/        domain types (mirror specs/domain)
  api/          typed REST client + mock adapter (mirror specs/api/rest-api.md)
  realtime/     WebSocket manager + mock event stream
  hooks/        TanStack Query queries + command mutations
  store/        Zustand UI store (selection, panels)
  components/
    ui/         shadcn-style primitives
    layout/     app shell, sidebar, topbar
    board/      Initiative drawers, columns, story cards
    story/      Story detail (timeline, tasks, human requests, decisions)
    task/       Task detail (execution attempts)
    attention/  Attention Queue
    artifacts/  Artifact viewer (renderer per type)
    notifications/
  pages/        routed pages (Board, Attention)
```

> The `components/ui` primitives follow shadcn/ui conventions but are
> dependency-light (no Radix) so the scaffold installs and builds cleanly. They
> can be replaced 1:1 with `npx shadcn@latest add ...` later.
