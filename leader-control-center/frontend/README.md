# Leader Control Center — Frontend

Supervision-first console for durable AI workflows. Implements the
[frontend spec](../_specs_/frontend/frontend.md): an **Initiative Kanban**, Story /
Task detail drawers, a global **Attention Queue**, a Notifications tray, and an
Artifact viewer.

The UI issues **business commands** (Start, Approve, Retry…) rather than CRUD,
mirroring the [REST API spec](../_specs_/api/rest-api.md), and never surfaces
workflow-engine internals. Condensed design rationale lives in
[`../_docs_/09-frontend.md`](../_docs_/09-frontend.md).

## Stack

- React 18 + TypeScript + Vite
- Tailwind CSS + shadcn/ui-style primitives (dependency-light, no Radix)
- TanStack Query (server state) + Zustand (UI state)
- React Router (routing)
- WebSocket realtime layer ([realtime spec](../_specs_/api/realtime.md))

## Run

```bash
npm install
npm run dev      # http://localhost:5173
```

By default a fresh checkout points at a **real backend** — `.env.local` sets
`VITE_USE_MOCKS=false` (start the backend first, see `../getting-started.md`).
For UI-only work, use the **in-browser mock backend** which also emits simulated
realtime events so the Board and Attention Queue update live:

```bash
echo "VITE_USE_MOCKS=true" > .env.local
npm run dev
```

Vite proxies `/api` (REST + WebSocket) to `http://localhost:8000` in dev, so no
CORS setup is needed. To point at a different backend, copy `.env.example` and
adjust `VITE_API_BASE_URL` / `VITE_WS_URL`.

## Scripts

- `npm run dev` — dev server (HMR)
- `npm run build` — `tsc --noEmit` + production build
- `npm run typecheck` — `tsc --noEmit`
- `npm run preview` — serve the production build
- `npm run lint` — ESLint

## Structure

```text
src/
  types/domain.ts     domain types — mirror the backend JSON contract 1:1
                      (backend/app/domain/models.py). camelCase on the wire.
  api/
    types.ts          ApiClient interface (the command-oriented API surface)
    index.ts          selects mock vs http client from VITE_USE_MOCKS
    http.ts           typed REST client (real backend)
    mock/             in-browser mock: mockClient.ts + server.ts (seed + logic)
  realtime/           WebSocket manager (ws.ts) + mock stream + RealtimeProvider
  hooks/              TanStack Query queries.ts, command mutations.ts, queryKeys.ts
  store/ui.ts         Zustand UI store (selection, open drawers/sheets)
  lib/utils.ts        cn() and small helpers
  pages/              routed pages: BoardPage, AttentionPage
  components/
    ui/               shadcn-style primitives (button, card, sheet, tabs, badge…)
    layout/           AppShell, Sidebar, Topbar
  features/           feature modules (one folder per domain area)
    board/            InitiativeBoard, BoardColumn, StoryCard, AddStoryCard
    story/            Story/Task detail sheets, TaskList, Timeline, DecisionList,
                      CreateStorySheet
    decisions/        HumanRequestCard
    artifacts/        ArtifactList, ArtifactSheet, ArtifactViewer (per-type render)
    notifications/    NotificationsSheet
  App.tsx             router (/, /attention)
  main.tsx            app entry (QueryClient, RealtimeProvider)
```

## How data flows

- **Reads:** components call TanStack Query hooks (`hooks/queries.ts`) → `api`
  client → backend (or mock).
- **Writes:** command mutations (`hooks/mutations.ts`) call the `api` client, then
  invalidate affected query keys.
- **Realtime:** `RealtimeProvider` subscribes to the WebSocket; incoming messages
  invalidate the relevant queries so the UI re-fetches. No manual polling.

> The `components/ui` primitives follow shadcn/ui conventions but are
> dependency-light so the scaffold installs and builds cleanly. They can be
> replaced 1:1 with `npx shadcn@latest add ...` later.
