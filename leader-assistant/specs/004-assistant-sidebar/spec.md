# Feature Specification: Assistant Sidebar (workspace, files, upload, sessions)

**Feature ID:** `004-assistant-sidebar`
**Status:** Draft
**Created:** 2026-08-16 · **Last Updated:** 2026-08-16

> Describes **what** and **why**. Adds a **collapsible left sidebar** to the human web UI
> delivered by feature [`003-assistant-ui`](../003-assistant-ui/spec.md), giving the operator
> workspace selection, a `vault/wiki/` file browser, local file/folder upload into the
> workspace's vault, and a list of prior conversations — all as surfaces over the REST API.
> **Extends** 003 (does not replace its chat surface). Primary spec references: [[13-api]],
> [[14-chat]], [[03-workspace]], [[04-knowledge-ingestion]], [[06-conversations]],
> [[17-observability]], [[09-planning]].

## Summary

A **collapsible left-side menu** for the web UI that consolidates workspace control and
workspace context beside the chat. From top to bottom it offers: a **workspace typeahead**
(with refresh and create-new-workspace icon buttons), a **read-only browser of the workspace's
`vault/wiki/` tree**, an **upload dropzone** that copies selected local files/folders into the
workspace's `vault/raw/` and ingests them (a progress bar replaces the dropzone during the run),
and a **Sessions panel** listing prior conversations the operator can reopen. Like 003, the
sidebar is a **pure presentation layer**: every read and effect goes **through the REST API over
HTTP** (P9). To support the sidebar, this feature also **adds the backing REST endpoints** the
API does not yet expose — list sessions, browse the `vault/wiki/` tree, and multipart
upload→`vault/raw/`→ingest — so parity is preserved (any capability the sidebar shows, the API
also offers).

## Goals

- Give the operator a single **collapsible sidebar** for workspace selection and context,
  alongside the existing chat surface (003), that can be hidden to maximize chat space.
- Let the operator **find and switch workspaces by typing** (typeahead over existing
  workspaces), and **create** a new workspace by name with an explicit action (P13).
- Show the **structure of the active workspace's `vault/wiki/`** as a browsable folder tree
  (navigation only — expand/collapse and view names; no edit).
- Let the operator **bring local knowledge in**: select files, a folder, or drag-and-drop,
  then upload them into the workspace's `vault/raw/` and **ingest** them, with visible progress
  (P2 create-only into `vault/raw/`, [[04-knowledge-ingestion]]).
- Let the operator **resume any prior conversation** for the active workspace from a **Sessions**
  list (P1 durable sessions, [[06-conversations]]).
- **Preserve interface parity (P9):** add REST endpoints for every new capability the
  sidebar surfaces, and keep the UI reaching the workspace only through those endpoints.

## Non-Goals

- No editing of `vault/wiki/` pages from the browser — the tree is **navigation only**; clicking
  a file does not open, edit, or reference its content in this feature (deferred).
- No overwrite or deletion of anything under `vault/raw/` — upload is **create-only**; existing
  raw sources are never mutated (P2).
- No new chat/planning behavior — chat, streaming, plan-first approval, and citations remain
  as specified by 002/003. This feature only adds sidebar surfaces and their endpoints.
- No authentication / multi-user accounts — the service stays local, single-operator.
- No direct filesystem access from the UI — all reads/writes go through the REST API (P9).
- No separate frontend build or second server/port — one process, one port (inherits 003).
- No deletion or renaming of workspaces from the sidebar (create + select only).

## User Scenarios

- **Scenario 1 — Collapse the sidebar and its panels:** As a user, I collapse the whole left
  menu to focus on the conversation, and expand it again when I need workspace context. I can also
  collapse each panel (**Vault**, **Wiki**, **Sessions**) on its own to hide the parts I'm not
  using without affecting the others.
- **Scenario 2 — Find a workspace by typing:** As a user, I start typing in the workspace box
  (which shows `workspace name` as gray placeholder when empty); matching existing workspaces
  appear as suggestions below the field, and picking one makes it the active workspace (P13).
- **Scenario 3 — Refresh the workspace list:** As a user who created a workspace elsewhere, I
  click the **refresh** icon button (icon-only, label on hover) to reload the list of workspaces.
- **Scenario 4 — Create a workspace:** As a user, I type a new name and click the **create new
  workspace** icon button (icon-only, label on hover); the workspace is created and becomes
  active, and its (empty) `vault/wiki/` tree is shown.
- **Scenario 5 — Browse the wiki:** As a user, I expand folders in the `vault/wiki/` panel to see
  how the active workspace's knowledge is organized, without changing anything.
- **Scenario 6 — Upload local knowledge:** As a user, I select files or a folder — or drag
  and drop them onto the panel — and submit; the files are copied into the workspace's
  `vault/raw/` and ingested. A **progress bar replaces the upload section** while this runs, then
  the panel returns and the `vault/wiki/` tree reflects any new pages produced by ingestion.
- **Scenario 7 — Resume a conversation:** As a user, I open the **Sessions** panel at the
  bottom of the sidebar, see my prior conversations for the active workspace listed
  most-recent-first under relative-date headers (Today, Yesterday, This Week, …), and select one to
  continue it in the chat (the chat resumes by `conversation_id`, [[06-conversations]]).
- **Scenario 7b — Start a new conversation:** As a user, I click **New conversation** at the top
  of the Sessions panel to begin a fresh chat thread, leaving my earlier conversations intact in
  the list below.
- **Scenario 8 — Empty states:** As a first-time user, an empty workspace shows an empty
  `vault/wiki/` tree and an empty Sessions list with clear "nothing yet" messaging rather than
  errors.

## Functional Requirements

Numbered, testable, unambiguous.

### Sidebar shell

- **FR-1:** The UI MUST present a **left-side menu** that the user can **collapse and expand**;
  its collapsed/expanded state MUST not affect the chat surface's functionality (003).
- **FR-2:** The sidebar MUST be composed, top to bottom, of **three independently collapsible
  panels**: (a) **Vault** (the workspace selector), (b) **Wiki** — which contains **both** the
  `vault/wiki/` file browser **and**, below it, the **upload** section (`Add files → raw/ +
  ingest`), and (c) **Sessions**. Each panel MUST be collapsible/expandable on its own without
  affecting the others.

### Workspace selector

- **FR-3:** The sidebar MUST show a **single-line text box** at the top that, when empty,
  displays the placeholder text **`workspace name`** in a muted/gray style.
- **FR-4:** As the user types, the UI MUST show **suggestions of existing workspaces** matching
  the input **below** the text box (typeahead), sourced from `GET /api/workspaces`. Selecting a
  suggestion MUST set it as the **active workspace** for the chat and the rest of the sidebar
  (P13).
- **FR-5:** To the **right** of the text box the UI MUST show **two icon-only buttons** that
  reveal a **text label on hover**: **Refresh** (reload the workspace list) and **Create new
  workspace**.
- **FR-6:** Activating **Create new workspace** MUST create a workspace named by the current
  text-box value via `POST /api/workspaces` **only on that explicit action**, then set it active
  and refresh the sidebar to reflect the new (empty) workspace. Empty or invalid names MUST
  surface a validation error, not a silent no-op.
- **FR-7:** The UI MUST make the **currently active workspace visible**; when none is selected,
  the sidebar and chat operate on the **default workspace** (P13).

### `vault/wiki/` file browser

- **FR-8:** Below the workspace selector the UI MUST show a **panel that browses the active
  workspace's `vault/wiki/` tree** as folders and files, fetched from a REST endpoint (see FR-15).
- **FR-9:** The file browser MUST be **navigation only**: folders expand/collapse and file
  names are shown/selectable, but this feature MUST NOT open, edit, or otherwise act on a
  file's content on click.
- **FR-10:** The file browser MUST scope strictly to the workspace's **`vault/wiki/`** subtree
  and MUST NOT expose `vault/raw/`, `sessions/`, `vault/output/`, `.git/`, or any path outside
  the workspace.

### Upload → `vault/raw/` → ingest

- **FR-11:** Within the same panel, below the browser, the UI MUST provide an **upload
  section** that lets the user pick **individual files**, pick a **folder**, or **drag and
  drop** files/folders.
- **FR-12:** On **submit**, the UI MUST send the selected files to a REST upload endpoint
  (see FR-16); the backend MUST write them into the active workspace's **`vault/raw/`**
  (create-only, never overwriting or editing existing raw content) and then **ingest** them
  ([[04-knowledge-ingestion]], P2).
- **FR-13:** While the upload+ingest runs, the UI MUST **replace the upload section with a
  progress indicator (progress bar)**; on completion it MUST restore the upload section and
  MUST **refresh the `vault/wiki/` browser** so newly produced pages appear.
- **FR-14:** Upload failures (rejected file, backend error, name collision under `vault/raw/`)
  MUST be **surfaced to the user**, and MUST NOT leave the workspace in a partially mutated state
  that violates the `vault/raw/` immutability invariant (P2).

### New REST endpoints (parity, P9)

- **FR-15:** The API MUST expose a read endpoint returning the **`vault/wiki/` tree** of a given
  workspace (folders + files, relative paths), consumed by the file browser. It MUST reveal only
  the `vault/wiki/` subtree (mirrors FR-10).
- **FR-16:** The API MUST expose an endpoint that accepts **uploaded files** (multipart /
  folder upload) for a given workspace, writes them under **`vault/raw/`** create-only, and
  **ingests** them, returning a result the UI can use to drive progress and refresh (mirrors
  FR-12/13).
- **FR-17:** The API MUST expose an endpoint that **lists prior conversations** for a given
  workspace (id + enough metadata to label each entry, e.g. title/first message and timestamp),
  consumed by the Sessions panel.
- **FR-18:** Every sidebar capability MUST be reachable through these REST endpoints; the UI
  MUST NOT import or call the capability layer, `app/vault`, `app/conversation`, or the
  filesystem directly (P9). New endpoints MUST live under `/api/*` and MUST NOT collide with
  existing routes or the Swagger UI at `/api/`.

### Sessions panel

- **FR-19:** At the **bottom** of the sidebar the UI MUST show a **Sessions** panel listing
  the active workspace's **prior conversations** (via FR-17), each selectable.
- **FR-20:** Selecting a session MUST **resume that conversation** in the chat by its
  `conversation_id` (feature 002/003 continuity, [[06-conversations]]).
- **FR-21:** Changing the active workspace MUST **re-scope** the `vault/wiki/` browser and the
  Sessions panel to that workspace.
- **FR-24:** A **New conversation** control MUST appear at the **top** of the Sessions panel
  (above the list), starting a fresh chat thread without a stored `conversation_id`.
- **FR-25:** Below the control, **all** prior conversations MUST be listed **reverse-chronologically**
  (most recent first) and **grouped under relative-date headers** — `Today`, `Yesterday`,
  `This Week`, `This Month`, `Older` — with empty groups omitted. Bucketing is derived from each
  conversation's `created` date.

### Cross-cutting

- **FR-22:** Selecting a workspace, browsing `vault/wiki/`, uploading, or resuming a conversation
  MUST NOT cause any **edit** of existing `vault/raw/` content or any edit of an existing
  `log.md` line; ingestion's appends to `log.md` and portal are the only permitted writes and are
  performed by the capability layer, not the UI (P2, P6, [[17-observability]]).
- **FR-23:** All sidebar panels MUST show sensible **empty and error states** rather than
  failing silently (no workspaces, empty `vault/wiki/`, no sessions, endpoint error).

## Key Entities & Concepts

- **Sidebar** — the collapsible left menu hosting the four stacked panels.
- **Workspace typeahead** — the top text box (placeholder `workspace name`) + suggestion list +
  refresh/create icon buttons, backed by `GET`/`POST /api/workspaces`.
- **Active workspace** — the workspace the chat and all sidebar panels currently operate on
  (P13); UI-held view state, the durable truth being the workspace itself (P1).
- **Wiki tree** — a read-only view of the active workspace's `vault/wiki/` folders and files
  (new read endpoint, FR-15).
- **Upload batch** — a set of local files/folders copied into `vault/raw/` create-only and then
  ingested (new upload endpoint, FR-16); its lifetime is shown by the progress bar.
- **Sessions list** — the active workspace's prior conversations, each with an id and a label,
  used to resume a thread (new list endpoint, FR-17; durable records in `sessions/`).

## Constraints & Assumptions

- **Constitution:** P1 (the workspace's vault is truth; UI holds only transient view state), P2
  (`vault/raw/` immutable — uploads are create-only, never overwrite/edit), P6 (traceability /
  citations preserved), P8 (human-in-the-loop — create-workspace and upload are explicit user
  actions), P9 (interface parity — sidebar is a surface over new REST endpoints), P10
  (portability — no new datastore; files land as Markdown/originals under `vault/raw/` + ingested
  `vault/wiki/`), P13 (multi-workspace) all apply.
- **Builds on** feature 003 (UI at `/`, Swagger at `/api/`) and feature 001 workspace/ingest
  capabilities. Reuses `GET`/`POST /api/workspaces`; **adds** wiki-tree, upload, and
  sessions-list endpoints.
- **Assumption:** single-operator, local use — no auth; the browser reaches the same-origin
  API without CORS. If this becomes multi-user, session isolation and upload authz must be
  revisited.
- **Assumption:** uploaded originals are acceptable to store under `vault/raw/` as-is; ingestion
  handles supported formats and reports unsupported ones rather than failing the whole batch.
- **Assumption:** browsers cannot recurse arbitrary local folders without user selection; a
  "select folder" affordance depends on browser support and is treated as best-effort
  alongside file selection and drag-and-drop.

## Acceptance Criteria

- [ ] **AC-1:** The web UI shows a **collapsible left sidebar** that can be hidden and
  restored without breaking chat, composed of **three independently collapsible panels** —
  **Vault**, **Wiki** (which nests the `vault/wiki/` browser and the upload section), and
  **Sessions** — each collapsible on its own. (FR-1, FR-2)
- [ ] **AC-2:** The workspace box shows the gray **`workspace name`** placeholder when empty;
  typing shows **matching existing workspaces** below it, and selecting one switches the active
  workspace. (FR-3, FR-4, FR-7)
- [ ] **AC-3:** Two **icon-only** buttons with **hover labels** appear to the right of the
  box; **Refresh** reloads the workspace list and **Create new workspace** creates the typed name
  via `POST /api/workspaces`, then makes it active. (FR-5, FR-6)
- [ ] **AC-4:** The **`vault/wiki/` browser** displays the active workspace's folders/files, is
  **navigation only**, and never shows `vault/raw/`, `sessions/`, `vault/output/`, or paths
  outside the workspace. (FR-8, FR-9, FR-10, FR-15)
- [ ] **AC-5:** Selecting files, a folder, or dragging-and-dropping and submitting **uploads
  the files into `vault/raw/` (create-only) and ingests them**; the workspace's `vault/raw/`
  gains the originals and `vault/wiki/` reflects produced pages. (FR-11, FR-12, FR-16)
- [ ] **AC-6:** During upload+ingest a **progress bar replaces the upload section**, then the
  section returns and the `vault/wiki/` browser refreshes. (FR-13)
- [ ] **AC-7:** The **Sessions** panel has a **New conversation** control at the top, then lists
  all prior conversations for the active workspace **most-recent-first, grouped under relative-date
  headers** (Today / Yesterday / This Week / This Month / Older, empty groups omitted); selecting
  one **resumes** that conversation in the chat and New conversation starts a fresh thread.
  (FR-17, FR-19, FR-20, FR-24, FR-25)
- [ ] **AC-8:** Changing the active workspace **re-scopes** the `vault/wiki/` browser and
  Sessions panel. (FR-21)
- [ ] **AC-9:** The sidebar makes **only HTTP calls to `/api/*`**; it imports no
  capability/vault/conversation module and touches no workspace file directly. (FR-18, P9)
- [ ] **AC-10:** No upload or navigation **edits existing `vault/raw/` content or an existing
  `log.md` line**; a raw name collision is reported without mutating existing content.
  (FR-14, FR-22, P2)
- [ ] **AC-11:** Empty and error states are shown for no-workspaces, empty `vault/wiki/`, no
  sessions, and endpoint failures. (FR-23)

## Resolved Decisions

- **D1 — Relationship to 003:** this is a **new feature (004) that extends 003**; 003's chat
  surface and workspace picker stay, and 004 adds the richer sidebar around them. *(User
  decision.)*
- **D2 — New endpoints in scope:** this feature **includes the backing REST endpoints**
  (wiki-tree browse, multipart upload→`vault/raw/`→ingest, sessions list) so the sidebar keeps
  parity (P9) rather than assuming pre-existing endpoints. *(User decision.)*
- **D3 — Workspace box behavior:** the top text box is a **typeahead over existing workspaces**;
  selecting a suggestion switches the active workspace, and **Create new workspace** creates a
  workspace named by the typed text. *(User decision.)*
- **D4 — File browser behavior:** the `vault/wiki/` browser is **navigation only**; clicking a
  file does not open/edit/reference it in this feature. *(User decision.)*
- **D5 — Upload target & P2 amendment:** uploaded files land under **`vault/raw/<provenance>/`**
  and are then ingested through the existing pipeline. This required **amending Constitution
  P2** (v1.1.0): `vault/raw/` is now **human-owned** — the app may add/modify/delete raw sources
  on the human's behalf — while the **internal ingestion process still MUST NOT mutate
  `vault/raw/`**. The `guard_write_path` guard is retained for all internal writers (ingest,
  portal, log, sessions); uploads use a **separate sanctioned human channel**
  (`capabilities.deposit_raw`) that writes to `vault/raw/` directly and validates against path
  traversal. *(User decision.)*

## Open Questions

Deferred to [`plan.md`](plan.md) (non-blocking):

- Exact **wiki-tree endpoint shape** (nested tree vs. flat relative-path list) and whether it
  reuses/extends the existing `/api/spec` reader.
- **Upload transport** details: multipart field naming, folder-path preservation under
  `vault/raw/`, per-file vs. batch ingest, and how granular the progress signal is (per-file vs.
  overall).
- Whether the **Sessions list** endpoint returns derived labels (first user message /
  timestamp) or requires a new stored title, and its ordering/pagination.
- Provenance value assigned to uploaded sources (e.g. `upload`) and handling of unsupported
  file types during ingest.

## Review Checklist

- [ ] No implementation details (how) leaked into this spec.
- [ ] Every requirement is testable.
- [ ] Scenarios cover the golden path and key edge cases.
- [ ] Complies with `memory/constitution.md`.
- [ ] Parity preserved: every sidebar capability is backed by a REST endpoint (P9).
