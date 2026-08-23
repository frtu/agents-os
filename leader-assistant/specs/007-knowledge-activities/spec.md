# Feature Specification: Knowledge activities — capture vs ingest, bottom-up

**Feature ID:** `007-knowledge-activities`
**Status:** Draft
**Created:** 2026-08-22 · **Last Updated:** 2026-08-22

> **Scope:** the **capture & ingestion flow only**. Query (`second-brain-query`) is a
> **follow-up** feature that will reuse the same activity interface; it is out of scope here.
>
> Describes **what** and **why**. Splits the two conflated notions **capture** (a raw input
> mechanism, no processing) and **ingest** (the internal knowledge workflow), and rebuilds
> ingest **bottom-up** on a reusable **activity** — the `second-brain-ingest` skill run
> headless behind a pydantic contract — that the app orchestrates but **never modifies**.
> Removes the constrained `mcp__leader__ingest` tool (superseding [[006-mcp-capability-tools]]
> FR-4 for `ingest`) whose narrow `{title,content,provenance}` shape and query-only browse
> made the agent refuse to run the real skill. Primary spec references: [[04-knowledge-ingestion]],
> [[03-workspace]], [[22-metadata-management]], [[13-api]], [[12-assistant]], [[10-risk-engine]].
> Builds on features
> [[002-assistant-chat]] (agent runtime), [[004-assistant-sidebar]] (upload), and
> [[006-mcp-capability-tools]] (agent MCP surface). Constitution: P2 (capture is the only
> sanctioned raw writer; ingest never mutates `vault/raw/`), P3 (one-directional pipeline),
> P9 (REST↔chat parity), P10 (git ledger).

## Background — the problem

The workspace's `second-brain-ingest` skill already knows how to turn raw sources into wiki
knowledge (PTCA decomposition, source summaries, portal/log, commit). But the app could not
run it:

1. **Wrong contract.** `capabilities.ingest` / the `mcp__leader__ingest` tool take
   `{title, content, provenance}` and write a single flat summary page. That is not "run the
   skill over captured sources"; it is a different, narrower operation.
2. **Over-restricted agent.** The persona guardrails ("retrieve only via `query`", "never
   browse `vault/raw/`") made the agent *refuse* to execute the skill even when asked (see the
   recorded failure in `_default_/sessions/caaa3aaf7d9e.md`).
3. **Layout mismatch.** The skill assumes a flat `raw/`, `wiki/`, `wiki/index.md`, and
   foundation docs at `docs/wiki-schema.md` / `docs/wiki-architecture.md`; the app uses
   `vault/raw/`, `vault/wiki/`, `vault/wiki/portal.md`, and had no `vault/docs/`.

This feature fixes all three by naming the two operations, giving ingest a proper layered
architecture, and reconciling the layout via injected context + copied foundation docs —
**without editing the skill**.

## Summary

- **Capture** is separated as an input-only mechanism (rename of the "human channel to
  `vault/raw/`" — `upload` / `deposit_raw`). It deposits sources into `vault/raw/<provenance>/`
  and performs **no processing**.
- **Ingest** becomes the internal **workflow** that reads captured sources and derives durable
  knowledge (`vault/raw/ → vault/wiki/`). It is built **bottom-up**:
  1. **Activity** — the compute unit, provided by the `second-brain-ingest` skill, run
     **headless** and **never modified**.
  2. **Activity interface** — a contract: an **Input Object** (parameters) and an **Output
     Object** (a **progress list** + an **error list**), both pydantic.
  3. **Implementation** — `activity_ingest.py`, a standalone wrapper ("uber package") that fits
     the interface and bridges to headless: it injects runtime context (chiefly the path
     mapping `raw/ ↔ {workspace}/vault/raw/`) around the skill, runs it, then coerces the
     skill's unstructured output into the pydantic Output Object.
  4. **Capability** — `capabilities.ingest` orchestrates: selects captured sources, invokes the
     activity through the interface, records the report, and falls back to the current
     in-process logic when the agent runtime is unavailable.
- **Foundation docs (option b).** On workspace create, `wiki-schema.md` and
  `wiki-architecture.md` are **copied verbatim** into `vault/docs/` (never modified), plus two
  **extension** docs (`wiki-schema-extension.md`, `wiki-architecture-extension.md`) that
  reference the foundation and may override paths for this workspace.
- **Remove `mcp__leader__ingest`.** The constrained ingest tool is deleted; ingest is invoked
  as the workflow above (superseding [[006-mcp-capability-tools]] FR-4/AC-1/AC-5 for `ingest`).

## Goals

- Name and separate **capture** (input, no processing) from **ingest** (internal workflow).
- Express ingest as a **bottom-up** layering: activity → interface → implementation →
  capability, so the reasoning lives in a reusable skill the app never rewrites.
- Define a stable **activity interface** (pydantic Input/Output Objects; Output = progress +
  errors) so any conforming activity is interchangeable.
- Provide `activity_ingest.py` as the **uber package** that injects context and runs the skill
  headless in **two phases** (run, then structure), returning the Output Object.
- Reconcile the skill's assumed layout with the workspace's real layout **without modifying the
  skill**, via injected path context and copied foundation + extension docs (option b).
- Remove `mcp__leader__ingest`; keep the P2 raw-write guard intact.

## Non-Goals

- **No editing of `second-brain-ingest`** (or any activity skill). Reconciliation is by injected
  context and docs only.
- **No event-driven watcher** — ingest is invoked on demand this feature; auto-trigger on file
  drop stays future ([[04-knowledge-ingestion]] §1).
- **No new risk rules / dreaming / spec-generation** — out of scope.
- **No change to REST/chat parity model** beyond removing the `ingest` tool and re-wiring the
  ingest capability; the two surfaces stay in parity (P9).
- **No general activity framework beyond ingest** — this feature defines the interface and
  applies it to ingest only. **Query is explicitly out of scope** (a follow-up feature will
  reuse the interface); this feature covers the **capture & ingestion flow only**.

## User Scenarios

- **Scenario 1 — Capture then ingest (UI path):** As a human I upload a file; it is **captured**
  into `vault/raw/notes/…` with no processing. Later I run ingest for the workspace; the ingest
  workflow reads the captured source(s) and produces wiki knowledge, portal/log updates, and a
  commit — and returns a report of progress and errors.
- **Scenario 2 — Ingest runs the real skill:** As an operator I trigger ingest; the workflow
  invokes the `second-brain-ingest` **activity** headless (unmodified), which browses
  `vault/raw/` via injected path context and writes under `vault/wiki/`. The agent no longer
  refuses (the old query-only restriction is gone for this workflow).
- **Scenario 3 — Structured report:** After an ingest run, the caller receives an Output Object
  with a **progress list** (what was processed / created / updated) and an **error list** (what
  failed and why), regardless of how verbose the skill's raw output was.
- **Scenario 4 — Layout reconciliation, skill untouched:** As a maintainer I confirm the skill
  file is byte-for-byte unchanged; the workspace's `vault/docs/*-extension.md` supply the path
  overrides (`raw/ → vault/raw/`, `wiki/ → vault/wiki/`, index `→ portal.md`) and the wrapper
  injects them as context.
- **Scenario 5 — Foundation docs on create:** As an operator I create a workspace; `vault/docs/`
  is populated with verbatim foundation docs and the two extension docs; the foundation copies
  are never modified afterward.
- **Scenario 6 — Offline fallback:** As an operator on a machine without the agent runtime, an
  ingest call still succeeds via the deterministic in-process fallback and returns a valid
  Output Object (degraded but conformant).
- **Scenario 7 — `mcp__leader__ingest` is gone:** As an operator, the agent no longer has a
  narrow `ingest` MCP tool; ingest happens through the workflow, and the raw-write guard still
  blocks any write under `vault/raw/`.
- **Scenario 8 — Backlog-driven selection:** As an operator I open `vault/wiki/tbd.md` and see
  unprocessed changes grouped by topic & theme. When I run ingest, the workflow processes items
  from `tbd.md`, checks off/removes what it completed, and records newly-discovered work back
  into the right topic section.

## Functional Requirements

Numbered, testable, unambiguous.

### Capture (input mechanism, no processing)

- **FR-1:** The human channel into `vault/raw/` MUST be named **capture**. The existing
  `deposit_raw` / `upload` behaviour is capture: it deposits sources into
  `vault/raw/<provenance>/` and performs **no** knowledge processing (no summary, no wiki write,
  no portal/log mutation).
- **FR-2:** Capture MUST remain the **only** sanctioned writer under `vault/raw/` (Constitution
  P2). The raw-write guard MUST stay in force for every other writer (agent, ingest workflow).
- **FR-3:** Capture and ingest MUST be **independently invocable**: capturing a source MUST NOT
  auto-run ingest, and ingest MUST operate over already-captured sources.

### Ingest as a bottom-up workflow

- **FR-4:** Ingest MUST be realized as a **workflow** over an **activity** (compute unit). The
  activity for ingest is the `second-brain-ingest` skill, run **headless**, and it MUST NOT be
  modified by the app.
- **FR-5:** The system MUST define an **activity interface** consisting of:
  - an **Input Object** (pydantic) carrying the activity's parameters (at minimum: the target
    workspace/vault path and the raw-path mapping/selection needed to run), and
  - an **Output Object** (pydantic) that is exactly a **progress list** and an **error list**.
  The interface MUST be activity-agnostic (not specific to ingest internals) so a conforming
  activity is interchangeable.
- **FR-6:** A standalone wrapper script **`activity_ingest.py`** MUST fit the activity interface
  and bridge to headless execution. It MUST:
  - **inject runtime context** into the activity — chiefly the path mapping between the skill's
    assumed layout (`raw/`, `wiki/`, index) and the workspace's real layout
    (`{workspace}/vault/raw/`, `{workspace}/vault/wiki/`, `portal.md`) — **without modifying the
    skill** (the "uber package");
  - run in **two phases**: (phase 1) create context, inject parameters, invoke the skill
    headless, and collect its **unstructured** output; (phase 2) call headless **again** to
    coerce that unstructured output into the pydantic **Output Object** (progress + errors);
  - return the Output Object to its caller.
- **FR-7:** The `capabilities.ingest` capability MUST become the ingest **workflow
  orchestrator**: resolve the workspace, invoke the activity via `activity_ingest.py` through the
  interface, and surface the Output Object as the ingest report. When the agent runtime is
  unavailable, it MUST fall back to a deterministic in-process ingest that still returns a valid
  Output Object (progress + errors), so the capability works offline (parity with the chat
  fallback model).
- **FR-8:** Ingest MUST continue to satisfy [[04-knowledge-ingestion]]: produce source
  summaries under `vault/wiki/sources/{provenance}/`, update `vault/wiki/portal.md`, append
  `vault/wiki/log.md`, and commit — and MUST NEVER write under `vault/raw/` (P2, FR-2).

### Foundation & extension docs (option b)

> The **rules, lifecycle, and file format** for these docs are owned by
> [[22-metadata-management]]. The FRs below state what feature 007 must implement to satisfy it.

- **FR-9:** On workspace create, `vault/docs/` MUST be populated with **verbatim copies** of the
  foundation docs `wiki-schema.md` and `wiki-architecture.md` from the **skill library's
  `references/`** (i.e. `skills/second-brain/references/{wiki-schema,wiki-architecture}.md`, the
  same source the skill was authored against). These copies are the **immutable core** and MUST
  NOT be modified by the app thereafter ([[22-metadata-management]] R1/R2).
- **FR-10:** On workspace create, `vault/docs/` MUST also contain `wiki-schema-extension.md` and
  `wiki-architecture-extension.md`, in the extension file format of [[22-metadata-management]] §4
  (header `extends`/`source`/`source-hash`/`copied`, plus Path-overrides / Added / Overridden /
  Removed sections). Each extension MUST **reference** its core and MAY **extend/override** it —
  at minimum recording the path overrides for this workspace (`raw/ → vault/raw/`,
  `wiki/ → vault/wiki/`, index `→ vault/wiki/portal.md`) ([[22-metadata-management]] R3/R4).
- **FR-11:** The activity wrapper (FR-6) MUST make the **overlaid** contract (core with the
  extension applied, extension-wins per [[22-metadata-management]] R5) available to the activity
  as injected context, so the skill resolves the correct paths **without being edited**.

### Remove the constrained ingest tool

- **FR-12:** The `mcp__leader__ingest` MCP tool MUST be **removed** (no longer registered on the
  agent MCP server, no longer in `allowed_tools`). This supersedes [[006-mcp-capability-tools]]
  FR-4/AC-1/AC-5 **for `ingest`**; the rest of feature 006's parity surface is unaffected.
- **FR-13:** The P2 raw-write guard hook MUST remain in force after the tool removal (writes
  under `vault/raw/` by the agent or ingest workflow are blocked).

### Tracking unprocessed work (`tbd.md`)

- **FR-14:** Selection of "unprocessed" work MUST be driven by a **`vault/wiki/tbd.md`** file —
  a maintained backlog of **unprocessed changes to the `vault/wiki/` folder**. The ingest
  workflow reads `tbd.md` to know what remains to be processed and updates it as items are
  handled (adding newly-discovered work, removing/checking off completed items). `tbd.md` is a
  normal wiki artifact (Markdown), committed with each ingest run.
- **FR-15:** `tbd.md` MUST be **classified by section**, where each section is a **topic &
  theme** grouping the related unprocessed changes. (Entries are organized under headings by
  topic/theme rather than as one flat list.)

## Key Entities & Concepts

- **Capture** — input-only deposit of a source into `vault/raw/<provenance>/`; no processing
  (FR-1). The sanctioned P2 raw writer.
- **Ingest workflow** — the orchestration in `capabilities.ingest` that turns captured sources
  into wiki knowledge via the activity (FR-7/FR-8).
- **Activity** — the compute unit; for ingest, the `second-brain-ingest` skill run headless,
  never modified (FR-4).
- **Activity interface** — pydantic **Input Object** (parameters) + **Output Object** (progress
  list + error list) (FR-5).
- **Implementation / uber package** — `activity_ingest.py`, which injects context around the
  skill and runs the two-phase headless bridge (FR-6).
- **Foundation docs** — `vault/docs/{wiki-schema,wiki-architecture}.md`, copied verbatim on
  create, immutable (FR-9).
- **Extension docs** — `vault/docs/{wiki-schema,wiki-architecture}-extension.md`, per-workspace
  overrides referencing the foundation (FR-10).
- **`tbd.md`** — `vault/wiki/tbd.md`, the maintained backlog of unprocessed `vault/wiki/`
  changes, sectioned by topic & theme; drives ingest's selection of unprocessed work
  (FR-14/FR-15).

## Constraints & Assumptions

- **Constitution:** P2 (capture is the only sanctioned raw writer; ingest/agent never mutate
  `vault/raw/`; guard preserved, FR-2/FR-13); P3 (one-directional pipeline preserved, FR-8);
  P9 (REST↔chat parity — ingest capability stays reachable from both surfaces, `ingest` tool
  removal applies to both); P10 (git ledger — ingest commits, FR-8). Amendment 1.1.1 introduces
  the capture terminology.
- **SDK assumption:** headless execution uses the `claude-agent-sdk` runtime (as in feature 002);
  the skill is discovered via the workspace's installed `skills/` (feature 005). When the runtime
  or credentials are absent, FR-7's offline fallback applies.
- **Skill immutability:** the app treats `second-brain-ingest` as a black box; all reconciliation
  is via injected context and `vault/docs/` (FR-6/FR-9/FR-10/FR-11).
- **Assumption:** single-operator, local, trusted machine (as in features 005/006).
- **Decided:** **query** (`second-brain-query`) is a **follow-up** — out of scope here (D9); the
  interface is designed so query can reuse it later.

## Acceptance Criteria

- [ ] **AC-1:** Capturing a source writes only under `vault/raw/<provenance>/` and produces no
  wiki/portal/log change; ingest is not auto-triggered. (FR-1, FR-3)
- [ ] **AC-2:** The activity interface exists as pydantic classes: an Input Object and an Output
  Object whose fields are a progress list and an error list. (FR-5)
- [ ] **AC-3:** `activity_ingest.py` runs the `second-brain-ingest` skill headless with injected
  path/context and returns an Output Object; the skill file is unmodified before/after. (FR-4,
  FR-6, FR-11, Scenario 4)
- [ ] **AC-4:** `activity_ingest.py` performs the two-phase bridge — phase 1 collects the skill's
  unstructured output; phase 2 coerces it into the pydantic Output Object. (FR-6)
- [ ] **AC-5:** `capabilities.ingest` orchestrates the activity and returns the report; with the
  runtime unavailable it falls back to deterministic in-process ingest and still returns a valid
  Output Object. (FR-7, Scenario 6)
- [ ] **AC-6:** An ingest run produces a `vault/wiki/sources/{provenance}/` summary, updates
  `portal.md`, appends `log.md`, commits, and writes nothing under `vault/raw/`. (FR-8, FR-2)
- [ ] **AC-7:** On workspace create, `vault/docs/` contains verbatim `wiki-schema.md` /
  `wiki-architecture.md` plus the two extension docs; the foundation copies are byte-identical to
  source and remain unmodified after an ingest run. (FR-9, FR-10)
- [ ] **AC-8:** The extension docs reference the foundation and encode the path overrides
  (`raw/ → vault/raw/`, `wiki/ → vault/wiki/`, index `→ portal.md`). (FR-10)
- [ ] **AC-9:** `mcp__leader__ingest` is not registered on the agent MCP server and not in
  `allowed_tools`; a write under `vault/raw/` by the agent or the ingest workflow is still
  blocked by the guard. (FR-12, FR-13, Scenario 7)
- [ ] **AC-10:** REST and chat both reach the ingest workflow (parity), and no other feature-006
  parity tool is removed. (FR-12, P9)
- [ ] **AC-11:** `vault/wiki/tbd.md` exists as the unprocessed-work backlog, organized into
  sections by topic & theme; an ingest run reads it, processes items, and updates it (completed
  items removed/checked, new work added under the right section), committed with the run.
  (FR-14, FR-15, Scenario 8)
- [ ] **AC-12:** Foundation docs copied on create are byte-identical to the skill library's
  `references/{wiki-schema,wiki-architecture}.md`. (FR-9)

## Resolved Decisions

- **D1 — Capture ≠ ingest:** the raw input channel (`upload`/`deposit_raw`) is renamed
  **capture** and does no processing; ingest is the separate internal workflow. *(User decision.)*
- **D2 — Bottom-up layering:** ingest is built from the activity up (activity → interface →
  implementation → capability); the skill is the compute unit and is never modified. *(User
  decision.)*
- **D3 — Output Object = progress + errors:** the activity's Output Object is exactly a progress
  list and an error list, as pydantic. *(User decision.)*
- **D4 — Two-phase headless bridge:** `activity_ingest.py` runs the skill, then calls headless
  again to structure the unstructured output into the Output Object. *(User decision.)*
- **D5 — Foundation docs option (b) + extensions:** copy `wiki-schema.md` /
  `wiki-architecture.md` into `vault/docs/` on create (immutable) and add `*-extension.md` docs
  that reference and can override the foundation (paths). *(User decision.)*
- **D6 — Inject context, don't edit the skill:** layout reconciliation is by injected path
  context + `vault/docs/`, never by modifying `second-brain-ingest`. *(User decision.)*
- **D7 — Remove `mcp__leader__ingest`:** the constrained ingest tool is deleted; ingest is the
  workflow. Supersedes feature 006 FR-4 for `ingest`. *(User decision.)*
- **D8 — Keep the raw-write guard:** P2 enforcement stays; capture is the only sanctioned raw
  writer. *(User decision.)*
- **D9 — Query is a follow-up:** this feature covers the **capture & ingestion flow only**.
  `second-brain-query` will reuse the activity interface in a later feature. *(User decision —
  resolves OQ-1.)*
- **D10 — Foundation docs source = skill library `references/`:** copy on create from
  `skills/second-brain/references/{wiki-schema,wiki-architecture}.md` (the source the skill was
  authored against), not the repo `_references_/`. *(User decision — resolves OQ-2; see FR-9.)*
- **D11 — Selection via `vault/wiki/tbd.md`:** unprocessed work is tracked in a maintained
  `tbd.md` backlog under `vault/wiki/`, classified by section (topic & theme); ingest reads and
  updates it rather than diffing `raw/` against `wiki/sources/`. *(User decision — resolves OQ-3;
  see FR-14/FR-15.)*

## Review Checklist

- [ ] No implementation details (how) leaked beyond the layered contract this feature defines.
- [ ] Every requirement is testable and maps to an AC.
- [ ] Scenarios cover the golden path and edge cases (offline fallback, skill immutability, guard).
- [ ] Complies with `memory/constitution.md` (P2 preserved via FR-2/FR-13; P3/P9/P10 held).
- [ ] Supersession of [[006-mcp-capability-tools]] FR-4 (ingest tool) is explicit (FR-12).
