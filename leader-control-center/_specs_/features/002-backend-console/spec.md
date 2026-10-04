# Feature Specification: Backend Console (Gradio)

**Feature ID:** `002-backend-console`
**Status:** Draft
**Created:** 2026-10-04 · **Last Updated:** 2026-10-04

**Amends:** [backend/architecture.md](../../backend/architecture.md) (Technology Stack, Module Boundaries) ·
[frontend/frontend.md](../../frontend/frontend.md) (Views → Backend Console)

## Summary

A lightweight, **read-only supervision console served by the backend itself**,
so a leader or developer can browse everything the Control Center holds without
starting the React frontend. A collapsible left sidebar carries three menus —
**Board** (Initiatives → Stories → Tasks), **Definitions** (Workflows,
Activities, Schedules) and **Executions** (Executions, Notifications,
Attention). Picking an entry shows its detail in the main area. The look and
interaction model mirror the sibling `leader-assistant` console (sidebar of
collapsible panels, entries rendered as clickable text trees).

## Goals

- Browse every planning object, definition, and runtime object from one page
  served on the backend port, with no Node toolchain.
- Show each object's detail (key fields, related objects, raw JSON) on click.
- Behave as just another client of the public REST API — it can never see or do
  more than the API allows.

## Non-Goals

- No commands: no Start, Approve, Retry, Create, Edit or Delete. Decisions are
  still answered in the React frontend or via the API (P1, P3).
- No realtime push; the operator refreshes explicitly.
- Does not replace the React frontend (Kanban, drawers, API Console).
- No new endpoints and no change to the wire contract.

## User Scenarios

- **Scenario 1 — Browse the board:** As a leader, I open `/ui`, expand **Board**,
  open an Initiative to see its Stories, open a Story to see its Tasks, and click
  a Task to read its goal, mode, status and dependencies.
- **Scenario 2 — Browse definitions:** I expand **Definitions** and click a
  Schedule; I see its human sentence, next occurrences and recent runs.
- **Scenario 3 — Check what is running:** I expand **Executions**, click an
  execution and see its status, progress, task executions, open decisions and
  timeline. Under **Attention** I see every open Human Request with its prompt.
- **Scenario 4 — Overview lists:** I click a group header (e.g. *Workflows*) and
  see all its entries as a table.
- **Scenario 5 — Bookmark:** I copy the URL after selecting an entry; opening it
  later shows the same entry.
- **Scenario 6 — Failure is explicit:** When the API rejects a read or is
  unreachable, the console says which read failed and why instead of showing an
  empty panel.

## Functional Requirements

- **FR-1:** The backend MUST serve the console at `/ui` on the API port, without
  shadowing `/api` (Swagger) or `/api/v1` (REST + WebSocket).
- **FR-2:** The console MUST have a collapsible left sidebar with three
  independently collapsible menus, top to bottom: **Board**, **Definitions**,
  **Executions**, plus a refresh control that reloads all three.
- **FR-3:** **Board** MUST list every Initiative (in board order) as an
  expandable node; under each, its Stories (by priority) with their board
  column; under each Story, its Tasks (by order).
- **FR-4:** **Definitions** MUST list three groups: **Workflows** (Workflow
  Definitions), **Activities** (Activity Definitions) and **Schedules**.
- **FR-5:** **Executions** MUST list three groups: **Executions** (the latest
  Story Execution of every Story that has one), **Notifications** (open
  notifications) and **Attention** (open Human Requests).
- **FR-6:** Every entry MUST render as clickable text (icon + label, truncated
  with the full name on hover), not as a button; groups are collapsible.
- **FR-7:** Clicking an entry MUST show, in the main area, a title, a readable
  summary of its key fields and related objects, and its raw JSON:
  - Initiative → description, Story count per board column, open Human Requests.
  - Story → description, priority, column, acceptance criteria, latest
    execution status, Tasks.
  - Task → planning mode, status, goal, success criteria, dependencies, capability.
  - Workflow Definition → input, definition.
  - Activity Definition → kind, timeout, script or webhook request.
  - Schedule → sentence, status, next occurrences, recent runs.
  - Execution → status, progress, task executions, open decisions, timeline.
  - Notification → type, status, message, time.
  - Human Request → Initiative/Story, type, priority, prompt, options, actions.
- **FR-8:** Clicking a group header MUST show all entries of that group as a table.
- **FR-9:** The console MUST obtain all data through the public REST API
  (`/api/v1`) only — never the application, infra, or engine layers directly.
- **FR-10:** A failed read MUST be shown in place, naming what was being read and
  the API's status and Problem+JSON `detail` (or transport error) (P9).
- **FR-11:** The selected entry MUST be reflected in the URL (`?item=…`) without
  reloading, and opening such a URL MUST show that entry.
- **FR-12:** The selected entry MUST be visibly marked in the sidebar.

## Key Entities & Concepts

Initiative, Story, Task, Workflow Definition, Activity Definition, Schedule,
Story Execution, Notification, Human Request (glossary terms). UI labels map:
*Workflows* = Workflow Definitions, *Activities* = Activity Definitions,
*Executions* = Story Executions, *Attention* = Attention Queue (P11).

## Commands, Queries & Events

None added. Uses existing queries: initiatives, initiative board, story tasks,
workflow/activity definitions, schedules + runs, execution + timeline + open
decisions, notifications, attention.

## Constraints & Assumptions

- Read-only; no business command is reachable from the console (P1, P3).
- The console reaches its own API over HTTP on the configured port; an override
  base URL is configurable for proxies.
- The data set is small (MVP seed scale), so per-Initiative/per-Story reads on
  refresh are acceptable.

## Acceptance Criteria

- [ ] AC-1 `GET /ui/` returns the console page; `/api` and `/api/v1/initiatives`
      still answer as before. (FR-1)
- [ ] AC-2 The page has a sidebar with Board, Definitions and Executions menus in
      that order and a refresh control. (FR-2)
- [ ] AC-3 The Board tree contains every seeded Initiative, its Stories, and
      their Tasks as clickable entries. (FR-3, FR-6)
- [ ] AC-4 The Definitions tree contains Workflows, Activities and Schedules
      groups with every seeded definition. (FR-4, FR-6)
- [ ] AC-5 The Executions tree contains Executions, Notifications and Attention
      groups, listing the started execution and every open Human Request. (FR-5, FR-6)
- [ ] AC-6 Opening an entry of each kind yields a title, a summary naming its
      key fields, and its raw JSON. (FR-7)
- [ ] AC-7 Opening a group header yields a table of its entries. (FR-8)
- [ ] AC-8 The console code imports nothing from the application, infra,
      workflow or domain layers. (FR-9)
- [ ] AC-9 A read that fails (unknown id, or API unreachable) shows the read, the
      status, and the detail. (FR-10)
- [ ] AC-10 An `?item=` deep link opens that entry on load. (FR-11)

## Open Questions

None.

## Review Checklist

- [x] No implementation details (how) leaked into this spec.
- [x] Every requirement is testable and has an id.
- [x] Scenarios cover the golden path and key edge cases.
- [x] Complies with [`constitution.md`](../../constitution.md).
- [x] Every amended area spec is listed under **Amends**.
