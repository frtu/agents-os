# AGENTS.md — Frontend

React supervision console for the Leader Control Center. Read this repo's root
[`../AGENTS.md`](../AGENTS.md) first for the domain model and project rules.

## Docs & specs

- **Constitution + spec-first workflow:** [`../_specs_/constitution.md`](../_specs_/constitution.md)
  · root [`../AGENTS.md`](../AGENTS.md#workflow--spec-first-mandatory). UI
  behaviour changes start in the feature spec (`../_specs_/features/NNN-*/`) and
  [`../_specs_/frontend/frontend.md`](../_specs_/frontend/frontend.md).

- Frontend overview & file tree: [`README.md`](README.md)
- Frontend spec: [`../_specs_/frontend/frontend.md`](../_specs_/frontend/frontend.md)
- API contract: [`../_specs_/api/rest-api.md`](../_specs_/api/rest-api.md) ·
  realtime: [`../_specs_/api/realtime.md`](../_specs_/api/realtime.md)
- Design rationale: [`../_docs_/09-frontend.md`](../_docs_/09-frontend.md)
- Running the stack: [`../getting-started.md`](../getting-started.md)

## Setup / run

```bash
./start.sh         # nvm Node + npm install + vite :5173 (proxy /api → :8010); --help
npm install
npm run dev        # http://localhost:5173 (vite proxies /api → :8010)
npm run typecheck  # tsc --noEmit
npm run build      # typecheck + production build
npm run lint
```

Backend selection via `VITE_USE_MOCKS` (see `.env.example`):

- `false` (default in `.env.local`) — real backend; start it first.
- `true` — in-browser mock backend that also emits simulated realtime events.

## Structure (see README for the full tree)

```text
src/
  types/domain.ts   domain types — mirror backend JSON contract 1:1 (camelCase)
  api/              ApiClient interface + mock/http clients (index picks by env)
  realtime/         WebSocket manager + RealtimeProvider
  hooks/            TanStack Query queries + command mutations + queryKeys
  store/ui.ts       Zustand UI state (selection, open drawers/sheets)
  pages/            BoardPage, AttentionPage, … ConsolePage (developer API Console)
  components/       ui/ (shadcn-style primitives), layout/ (AppShell…)
  features/         board · story · decisions · artifacts · notifications · console
```

## How data flows

- **Reads:** components → TanStack Query hooks (`hooks/queries.ts`) → `api` client.
- **Writes:** command mutations (`hooks/mutations.ts`) → `api` client, then
  invalidate affected query keys.
- **Realtime:** `RealtimeProvider` subscribes to the WS; messages invalidate
  queries so the UI re-fetches. No manual polling.

## How to start writing code

- New view/interaction: add a component under the right `features/` folder;
  routed pages live in `pages/` and are wired in `App.tsx`.
- New server call: extend the `ApiClient` interface (`api/types.ts`), implement
  in both `api/http.ts` and `api/mock/`, then add a query/mutation hook.
- New/changed data shape: update `src/types/domain.ts` and keep it 1:1 with
  backend `app/domain/models.py`.

## Conventions

- **Command-oriented UI.** Issue business commands (Start, Approve, Retry…),
  never surface workflow-engine internals.
- **Contract lockstep.** `types/domain.ts` must match the backend camelCase JSON.
- `components/ui` are dependency-light shadcn-style primitives (no Radix); they
  can be swapped 1:1 with `npx shadcn@latest add ...` later.
- **Cite the spec.** Components/hooks implementing a feature requirement carry
  `// spec NNN FR-N`.
- **Verification gate.** `npm run typecheck && npm run build` must pass; the
  typecheck is the contract test for `types/domain.ts` (P6). Exercise the
  feature's User Scenarios against the real backend (`VITE_USE_MOCKS=false`)
  and keep `api/mock/` in step so the mock backend shows the same behaviour.

