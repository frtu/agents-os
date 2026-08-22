# Feature Specification: Assistant Sidebar (workspace, files, upload, sessions)

**Feature ID:** `004-assistant-sidebar`
**Status:** Draft
**Created:** 2026-08-16 · **Last Updated:** 2026-08-22

> Describes **what** and **why**. Adds a **collapsible left sidebar** to the human web UI
> delivered by feature [`003-assistant-ui`](../003-assistant-ui/spec.md), giving the operator
> workspace selection, a `vault/wiki/` file browser, local file/folder upload into the
> workspace's vault, and a list of prior conversations — all as surfaces over the REST API.
> **Extends** 003 (does not replace its chat surface). Primary spec references: [[13-api]],
> [[14-chat]], [[03-workspace]], [[04-knowledge-ingestion]], [[06-conversations]],
> [[17-observability]], [[09-planning]].

## Summary

A **collapsible left-side menu** for the web UI that consolidates workspace control and
workspace context beside the chat. From top to bottom it offers: a **Workspaces** panel (an
**`Active`** indicator on top, a name box that opens a **picker of the other workspaces** when
clicked, a **create** button that appears only when the name is changed, and a **refresh**
button), a **read-only browser of the workspace's
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
- Let the operator **find and switch workspaces from a picker** — clicking the name box opens a
  list of the other workspaces (typing narrows it) — and **create** a new workspace by name with an
  explicit action shown only when the name is changed (P13).
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
  collapse each panel (**Workspaces**, **Wiki**, **Sessions**) on its own to hide the parts I'm not
  using without affecting the others.
- **Scenario 2 — Switch workspace from the picker:** As a user, I **click the workspace-name box**
  and see a **select box of all the other workspaces**; if there are none, it shows **`<none>`**.
  Typing narrows the list. Picking one makes it the active workspace (P13), and the **`Active`**
  indicator at the top of the panel updates.
- **Scenario 3 — Refresh from the backend:** As a user who changed workspaces elsewhere, I click
  the **refresh** icon button at the **rightmost** of the name row (icon-only, label on hover) to
  re-fetch the workspace list and re-render the panel and wiki browser (names, tooltips, `Active`)
  from the backend.
- **Scenario 4 — Create a workspace:** As a user, I **edit the name** in the box; as soon as it
  **differs from the active name**, a **create** (`+`) icon button appears to the **right** of the
  box (hidden until then). I click it, and the workspace is created and becomes active, and its
  (empty) `vault/wiki/` tree is shown.
- **Scenario 5 — Browse the wiki:** As a user, I expand folders in the `vault/wiki/` panel to see
  how the active workspace's knowledge is organized, without changing anything.
- **Scenario 6 — Upload local knowledge:** As a user, I select files or a folder — or drag
  and drop them onto the panel — and submit; the files are copied into the workspace's
  `vault/raw/` and ingested. A **progress bar replaces the upload section** while this runs, then
  the panel returns and the `vault/wiki/` tree reflects any new pages produced by ingestion.
- **Scenario 7 — Resume a conversation:** As a user, I open the **Sessions** panel at the
  bottom of the sidebar, see my prior conversations for the active workspace listed
  most-recent-first under relative-date headers (Today, Yesterday, This Week, …) as **clickable
  text entries**, and click one to continue it in the chat (the chat resumes by
  `conversation_id`, [[06-conversations]]).
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
  panels**: (a) **Workspaces** (the workspace selector), (b) **Wiki** — which contains **both** the
  `vault/wiki/` file browser **and**, below it, the **upload** section (`Add files → raw/ +
  ingest`), and (c) **Sessions**. Each panel MUST be collapsible/expandable on its own without
  affecting the others.

### Workspaces panel (selector + create)

- **FR-3:** The **Workspaces** panel MUST show a **single-line text box** for the workspace name.
  The box MUST be **pre-filled with the active workspace's name**; when the box is empty it MUST
  display the placeholder text **`workspace name`** in a muted/gray style. This box is both the
  **selection trigger** (FR-4) and the **create-name input** (FR-6); its pre-filled value is the
  **original** value referenced by FR-5/FR-6.
- **FR-4 (selection):** **Clicking (focusing) the text box** MUST reveal a **select box listing
  all the other existing workspaces** — every workspace except the currently active one — sourced
  from `GET /api/workspaces`. If there are **no other workspaces**, the select box MUST display a
  single non-selectable entry **`<none>`**. Typing MUST **narrow** the list to matching names.
  Choosing an entry MUST set it as the **active workspace** for the chat and the rest of the
  sidebar (P13) and MUST update the `Active` indicator (FR-7).
- **FR-5 (controls & layout):** On the **same row as the text box**, to its **right**, the panel
  MUST place, left-to-right: a **Create** (`+`) icon button and, at the **rightmost** position, a
  **Refresh** icon button. Both MUST be **icon-only with a text label on hover**. The **Create**
  (`+`) button MUST be **shown only when the text-box value differs from the original**
  (pre-filled active name); when the value is unchanged or empty the Create button MUST be
  **hidden**. The **Refresh** button MUST be **always visible** and MUST re-fetch state from the
  backend and re-render the panel and the `vault/wiki/` browser — workspace list, `Active`
  indicator, names, and hover tooltips — so changes made **elsewhere** are reflected.
- **FR-6 (creation):** Activating **Create** (`+`) MUST create a workspace named by the current
  text-box value via `POST /api/workspaces` **only on that explicit action**, then set it active
  and refresh the panel to reflect the new (empty) workspace and its `Active` indicator. Because
  Create is visible only when the name was modified from the original (FR-5), it always targets a
  **new** name. Empty or invalid names MUST surface a validation error, not a silent no-op.
- **FR-7 (active indicator):** The panel MUST show the **currently active workspace** in an
  **`Active`** indicator (renamed from `Active vault`) placed at the **top of the Workspaces
  panel, above the text box**. When no workspace is selected, the sidebar and chat operate on the
  **default workspace** (P13), which the `Active` indicator MUST name.

### `vault/wiki/` file browser

- **FR-8:** Below the workspace selector the UI MUST show a **panel that browses the active
  workspace's `vault/wiki/` tree** as folders and files, fetched from a REST endpoint (see FR-15).
- **FR-9:** The file browser MUST be **navigation only**: folders expand/collapse and file
  names are shown/selectable, but this feature MUST NOT open, edit, or otherwise act on a
  file's content on click.
- **FR-9b:** Each folder and file name MUST render on a **single line** — it MUST NOT wrap to a
  second line when it reaches the panel border. A name too long for the available width MUST be
  **truncated with a trailing ellipsis** rather than wrapped or overflowing. Truncation MUST NOT
  remove the folder's expand/collapse disclosure control. Hovering a **file** MUST reveal the
  **full file name** in a tooltip (the *file tooltip*); hovering a **folder** MUST likewise reveal
  the **full folder name** (the *folder tooltip*). The tooltip MUST carry the untruncated name
  regardless of whether the visible label was truncated, and MUST NOT be clipped by the panel's
  own scroll bounds.
- **FR-10:** The file browser MUST scope strictly to the workspace's **`vault/wiki/`** subtree
  and MUST NOT expose `vault/raw/`, `sessions/`, `vault/output/`, `.git/`, or any path outside
  the workspace.
- **FR-10a:** The tree MUST list **only folders that contain data**. A folder whose subtree holds
  no files (empty, or containing only empty subfolders) MUST be omitted from the tree. Pruning is
  applied in the read endpoint (FR-15) so both surfaces stay in parity.

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
  the active workspace's **prior conversations** (via FR-17), each selectable. Each
  conversation entry MUST render as **clickable text** (a selection affordance), NOT as an
  action button — resuming a past conversation is a selection, not a command. Each entry MUST
  be prefixed with a **discussion/chat icon** to signal it is a conversation. The **New
  conversation** control (FR-24) remains a button because it performs an action.
- **FR-20:** Selecting a session MUST **resume that conversation** in the chat by its
  `conversation_id` (feature 002/003 continuity, [[06-conversations]]).
- **FR-21:** Changing the active workspace MUST **re-scope** the `vault/wiki/` browser and the
  Sessions panel to that workspace.
- **FR-24:** A **New conversation** control MUST appear at the **top** of the Sessions panel
  (above the list), starting a fresh chat thread without a stored `conversation_id`.
- **FR-25:** Below the control, **all** prior conversations MUST be listed **reverse-chronologically**
  (most recent first) and **grouped under relative-date headers** — `Today`, `Yesterday`,
  `This Week`, `This Month`, `Older` — with empty groups omitted. Bucketing is derived from each
  conversation's `created` date. Each listed conversation MUST render as **clickable text**
  (per FR-19), not as an action button. Each relative-date group MUST be an **independently
  collapsible section** (its conversations expand/collapse) and MUST be **expanded by default**.

### Cross-cutting

- **FR-22:** Selecting a workspace, browsing `vault/wiki/`, uploading, or resuming a conversation
  MUST NOT cause any **edit** of existing `vault/raw/` content or any edit of an existing
  `log.md` line; ingestion's appends to `log.md` and portal are the only permitted writes and are
  performed by the capability layer, not the UI (P2, P6, [[17-observability]]).
- **FR-23:** All sidebar panels MUST show sensible **empty and error states** rather than
  failing silently (no workspaces, empty `vault/wiki/`, no sessions, endpoint error).

## Key Entities & Concepts

- **Sidebar** — the collapsible left menu hosting the stacked panels.
- **Workspaces panel** — an **`Active`** indicator on top, then a workspace-name box that opens a
  **picker of the other workspaces** on click (**`<none>`** when there are none), a **create**
  (`+`) button shown only when the name is changed, and an always-visible **refresh** button;
  backed by `GET`/`POST /api/workspaces`.
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
  **Workspaces**, **Wiki** (which nests the `vault/wiki/` browser and the upload section), and
  **Sessions** — each collapsible on its own. (FR-1, FR-2)
- [ ] **AC-2:** The Workspaces panel shows an **`Active`** indicator at the **top**; the name box
  is pre-filled with the active name (gray **`workspace name`** placeholder when empty). **Clicking
  the box** opens a **select of all other workspaces** (or **`<none>`** when there are none);
  typing narrows it, and choosing one switches the active workspace and updates `Active`.
  (FR-3, FR-4, FR-7)
- [ ] **AC-3:** On the name row, **icon-only** buttons with **hover labels** sit to the right: a
  **Create** (`+`) button **visible only when the box value differs from the active name** (hidden
  otherwise), and, at the **rightmost**, an always-visible **Refresh** button that re-fetches from
  the backend and re-renders the panel and wiki browser (list, `Active`, tooltips). Create makes
  the typed name active via `POST /api/workspaces`. (FR-5, FR-6)
- [ ] **AC-4:** The **`vault/wiki/` browser** displays the active workspace's folders/files, is
  **navigation only**, lists **only folders that contain data** (empty folders omitted), and never
  shows `vault/raw/`, `sessions/`, `vault/output/`, or paths outside the workspace.
  (FR-8, FR-9, FR-10, FR-10a, FR-15)
- [ ] **AC-4a:** Every `vault/wiki/` folder and file name renders on **one line** (no wrap),
  truncating with a trailing ellipsis when too wide; hovering a file shows its **full name** in a
  tooltip and hovering a folder shows its **full folder name** in a tooltip. (FR-9b)
- [ ] **AC-5:** Selecting files, a folder, or dragging-and-dropping and submitting **uploads
  the files into `vault/raw/` (create-only) and ingests them**; the workspace's `vault/raw/`
  gains the originals and `vault/wiki/` reflects produced pages. (FR-11, FR-12, FR-16)
- [ ] **AC-6:** During upload+ingest a **progress bar replaces the upload section**, then the
  section returns and the `vault/wiki/` browser refreshes. (FR-13)
- [ ] **AC-7:** The **Sessions** panel has a **New conversation** control (a button) at the top,
  then lists all prior conversations for the active workspace as **clickable text prefixed with a
  discussion icon**, **most-recent-first, grouped under relative-date headers** (Today / Yesterday /
  This Week / This Month / Older, empty groups omitted) where **each date group is an independently
  collapsible section** (expanded by default); clicking one **resumes** that conversation in the chat
  and New conversation starts a fresh thread. (FR-17, FR-19, FR-20, FR-24, FR-25)
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
- **D3 — Workspaces panel behavior:** the panel is titled **Workspaces**; an **`Active`**
  indicator (renamed from `Active vault`) sits at the **top**, above the name box. **Clicking** the
  name box opens a **select of all other workspaces** (**`<none>`** when there are none) and
  choosing one switches the active workspace; typing narrows the list. A **Create** (`+`) button to
  the **right** of the box appears **only when the name is changed** from the active (original) name
  and creates that new workspace; an always-visible **Refresh** button at the **rightmost** re-syncs
  the panel and wiki browser from the backend. *(User decision, 2026-08-22.)*
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
