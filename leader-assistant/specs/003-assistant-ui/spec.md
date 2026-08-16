# Feature Specification: Assistant Web UI

**Feature ID:** `003-assistant-ui`
**Status:** Draft
**Created:** 2026-08-16 · **Last Updated:** 2026-08-16

> Describes **what** and **why**. Adds a **human-facing web UI** as a surface over the
> REST API delivered by feature [`002-assistant-chat`](../002-assistant-chat/spec.md) and the
> capability layer of [`001-leader-assistant`](../001-leader-assistant/tasks.md). This
> feature **revisits and supersedes** the GUI Non-Goal declared in feature 002 §Non-Goals.
> Primary spec references: [[13-api]], [[14-chat]], [[12-assistant]], [[00-product-vision]],
> [[09-planning]], [[03-vault]].

## Summary

A minimal web UI, served at the **root URL** as the default **startup surface**, that lets
a human chat with the assistant (the project's AI Product Owner) and pick or create the
vault the conversation operates on. The UI is a **pure presentation layer**: it holds no
business logic and reaches the vault only by **calling the backend REST API** over HTTP
(`/api/chat`, `/api/chat/stream`, `/api/vaults`). Because it adds no capability the API
lacks, it preserves interface parity (Constitution P9). It runs in the **same process and
port** as the API. The interactive **Swagger UI moves to `/api/`**, freeing `/` for the UI.

## Goals

- Make the assistant usable by a human **without curl/Swagger** — open the base URL and chat.
- Serve the UI at `/` as the **default startup mode**; move Swagger to `/api/`.
- Keep the UI a **thin surface over the REST API** (P9): it calls the API, never the vault
  or capability layer directly.
- Support **streamed** replies so long answers appear incrementally.
- Let the user **pick, create, and switch** the active vault (P13), defaulting when none is
  chosen.
- Preserve **conversation continuity** — resume a thread via the returned `conversation_id`.
- Honor **plan-first governance** (P8): when the assistant returns a `pending_plan`, the UI
  shows it and requires an **explicit approval action** before execution; no auto-approval.
- Show the **citations** returned with each answer so the human can verify claims.

## Non-Goals

- No new capabilities, engines, or data paths — the UI only presents what the API already
  offers (P9). Dreaming, risk-branching, ingestion pipelines, spec generation are untouched.
- No authentication / multi-user accounts — the service remains local, single-operator.
- No direct vault/filesystem access from the UI — all reads/writes go through the REST API.
- No full capability console in this feature — ingest, lint, spec-read, standalone query,
  and output production panels are **out of scope** here (candidate follow-up feature).
- No separate frontend build toolchain or second server/port — one process, one port.

## User Scenarios

- **Scenario 1 — Open and chat:** As a user, when I open the base URL, I land directly on
  the chat UI (startup mode) and can ask a question, so that I can use the assistant without
  touching the API by hand.
- **Scenario 2 — Streamed answer:** As a user, when I ask a broad question, I watch the
  answer stream in progressively, so that long responses feel responsive.
- **Scenario 3 — Continue a thread:** As a user, when I send a follow-up, the UI reuses the
  conversation id from the previous turn so the assistant answers in context, without me
  managing ids.
- **Scenario 4 — Pick a vault:** As a user working across projects, I select the vault from
  a list before chatting; if I pick none, the default vault is used (P13).
- **Scenario 5 — Create a vault:** As a user, I explicitly create a new vault from the UI,
  which calls the vault-creation API; the new vault then appears in the picker.
- **Scenario 6 — Approve consequential work:** As a stakeholder, when my request is
  consequential and the assistant returns a plan, the UI shows the plan and an **Approve**
  control; only when I click it does the UI resend the turn with approval to execute (P8).
- **Scenario 7 — Find the API docs:** As a developer, when I go to `/api/`, I get the
  Swagger UI to explore the same capabilities the chat UI uses.

## Functional Requirements

Numbered, testable, unambiguous.

- **FR-1:** The system MUST serve a human-facing web UI at the **root path `/`** as the
  default surface when the service starts.
- **FR-2:** The interactive API docs (Swagger UI) MUST be served under **`/api/`**; the REST
  capability endpoints MUST remain reachable under `/api/<resource>` (e.g. `/api/chat`,
  `/api/vaults`) without conflict.
- **FR-3:** The UI MUST obtain all data and effects by **calling the REST API over HTTP**
  (same origin). It MUST NOT import or call the capability layer, `app/vault`, or the
  filesystem directly (P9; keeps the UI a presentation surface and dogfoods the API).
- **FR-4:** The UI MUST let the user send a chat message and MUST render the reply
  **incrementally** by consuming the streaming endpoint (`/api/chat/stream`, SSE), falling
  back to the full-reply endpoint (`/api/chat`) if streaming is unavailable.
- **FR-5:** The UI MUST maintain **conversation continuity** by capturing the
  `conversation_id` returned by the API and sending it on subsequent turns, so the thread
  resumes in context (FR-3/FR-13 of feature 002).
- **FR-6:** The UI MUST let the user **view the list of vaults** (via `GET /api/vaults`),
  **select** the active vault for the conversation, and **create** a vault (via
  `POST /api/vaults`) **only on an explicit user action**.
- **FR-7:** When no vault is selected, chat turns MUST operate on the **default vault**
  (P13); the UI MUST make the active vault visible to the user.
- **FR-8:** When an API reply includes a **`pending_plan`** (consequential request), the UI
  MUST display the plan and provide an **explicit approval control**; only when the user
  activates it does the UI resend the turn with `approve: true` to execute. The UI MUST NOT
  auto-approve (P8, [[09-planning]]).
- **FR-9:** The UI MUST display the **citations** returned with an answer so the human can
  verify factual claims (P6).
- **FR-10:** The UI MUST add **no capability** beyond what the REST API exposes, and MUST
  run in the **same process/port** as the API (single local service). (P9)
- **FR-11:** The UI MUST surface **errors** from the API (e.g. missing named vault, backend
  failure) to the user rather than failing silently.
- **FR-12:** Selecting or creating a vault, or resuming a conversation, MUST NOT cause any
  write under `raw/` or edit of an existing `log.md` line (those invariants are enforced by
  the API/capability layer; the UI only calls it). (P2, P6)

## Key Entities & Concepts

- **Startup surface** — the chat UI served at `/` that a human sees first.
- **Vault picker** — the UI control listing vaults and offering select/create, backed by
  `/api/vaults`.
- **Conversation state** — the UI-held `conversation_id` (+ active vault) used to keep a
  thread in context across turns; the durable record still lives in `sessions/` on the
  server (P1).
- **Pending plan panel** — the UI presentation of an API `pending_plan` plus the approval
  control (P8).
- **Citation list** — the UI presentation of the `citations` an answer returns.
- **API base** — the same-origin REST surface (`/api/*`) the UI calls; Swagger at `/api/`.

## Constraints & Assumptions

- **Constitution:** P1 (vault is truth — the UI holds only transient view state), P2 (`raw/`
  immutable), P6 (traceability / citations), P8 (human-in-the-loop approval), P9 (interface
  parity — UI is a surface over the API), P10 (portability — no new datastore), P13
  (multi-vault) all apply.
- Builds directly on feature 002's chat endpoints (`/api/chat`, `/api/chat/stream`) and
  feature 001's vault endpoints (`/api/vaults`). Adds a presentation surface, not a data path.
- **Assumption:** single-operator, local use — no auth. If this becomes multi-user, session
  isolation and identity must be revisited (mirrors feature 002 assumption).
- **Assumption:** the UI and API are same-origin (one process/port), so the UI calls the API
  without CORS or cross-host configuration.

## Acceptance Criteria

- [ ] **AC-1:** Requesting `/` returns the chat UI (the default startup surface); the UI
  loads without manually visiting any other path. (FR-1)
- [ ] **AC-2:** Swagger UI is served at `/api/`; `/api/chat` and `/api/vaults` still resolve
  to their endpoints (no route conflict). (FR-2)
- [ ] **AC-3:** Sending a message in the UI produces a reply that renders **incrementally**
  (streamed), and the same content is obtained via the non-streaming path when streaming is
  unavailable. (FR-4)
- [ ] **AC-4:** A follow-up message continues the **same conversation** (the UI reused the
  returned `conversation_id`), verified by a context-aware answer. (FR-5)
- [ ] **AC-5:** The vault picker lists existing vaults, lets the user switch the active
  vault, and creating a vault via the UI makes it appear in the list; with none selected the
  default vault is used. (FR-6, FR-7)
- [ ] **AC-6:** A consequential request shows a **plan** and an approval control; no mutation
  happens until the user approves, after which the turn is resent with `approve: true` and
  executes. (FR-8, P8)
- [ ] **AC-7:** Answers display their **citations** when the API returns them. (FR-9)
- [ ] **AC-8:** The UI makes **only HTTP calls to `/api/*`**; it imports no capability/vault
  module and touches no vault file directly (verified by inspection/test). (FR-3, FR-10, P9)
- [ ] **AC-9:** An API error (e.g. a missing named vault) is shown to the user in the UI,
  not swallowed. (FR-11)

## Resolved Decisions

- **D1 — UI stack:** the UI is a **Gradio** app **mounted on the existing FastAPI server**
  at `/` (one process/port), reviving the archived `__OLD__/` approach but re-pointed at the
  REST API. *(User decision.)*
- **D2 — Scope:** this feature delivers **chat + vault picker** (select/create/resume) only;
  a full capability console is deferred. *(User decision.)*
- **D3 — Coupling:** the UI calls the backend **over the HTTP REST API**, not the in-process
  capability layer, so it stays a pure presentation surface and continuously exercises the
  API (P9). *(Derived from FR-3.)*
- **D4 — Docs relocation:** Swagger UI moves from `/docs` to **`/api/`** and `/` becomes the
  UI; REST endpoints keep their `/api/<resource>` paths. *(User requirement.)*

## Open Questions

- None blocking. Deferred to [`plan.md`](plan.md): exact SSE-consumption mechanism inside
  the UI process (async HTTP client vs. shared in-process streaming) and whether `openapi.json`
  / ReDoc also relocate under `/api/`.

## Review Checklist

- [ ] No implementation details (how) leaked into this spec.
- [ ] Every requirement is testable.
- [ ] Scenarios cover the golden path and key edge cases.
- [ ] Complies with `memory/constitution.md`.
- [ ] Parity preserved: the UI exposes no capability the API lacks (P9).
