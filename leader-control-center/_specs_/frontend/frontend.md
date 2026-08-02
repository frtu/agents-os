# Frontend

The UI optimizes for **supervision**, not editing. Within seconds a leader should
answer:

- What is running?
- What needs me?
- What completed?
- Where are we blocked?

---

## Technology Stack

- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query (server state)
- Zustand (local UI state)
- WebSocket (realtime; see [../api/realtime.md](../api/realtime.md))
- react-jsonschema-form (renders a Workflow Definition's `input` JSON Schema as a
  form — see Create Story below)

---

## Primary Interface: Initiative Kanban

The primary view is a Kanban board. Each **Initiative** (backed by an Epic)
appears as a collapsible vertical drawer. Inside each Initiative, Stories are
organized by column:

```
Todo · Ready · Running · Blocked · Completed
```

These columns are a **UI projection** combining a Task/Story's planning state
with its latest execution status — they are not stored planning states (see
[../domain/state-machines.md](../domain/state-machines.md)).

---

## Navigation

The left sidebar lists the top-level destinations, in order:

```
Board · Workflow · Attention
```

`Workflow` sits directly below `Board` and opens the Workflow Definitions manager.

---

## Views

### Initiative Board
Collapsible drawers per Initiative; Stories as cards in columns; progress and
attention badges.

### Create Story
The Todo column ends with an add-story card (a centered `+`). It opens a
right-hand drawer scoped to the initiative's epic: a form on top (title `*`
required; description, priority, acceptance criteria optional) and a chat box at
the bottom whose textarea auto-grows per line, with a Send button at the
bottom-right. Sending a natural-language description asks the backend to prefill
the form (LLM-assisted); the user reviews, edits, and presses Create to add the
Story to Todo.

The form also has a **Use template** checkbox. When ticked, the drawer resolves
the Workflow Definition (the initiative's linked definition, or a select box to
choose one) and renders its `input` JSON Schema as a form via
react-jsonschema-form. On Create, the captured values are sent as `templateInput`
together with `workflowDefinitionId`; the schema form's own validation blocks
Create until the input is valid.

### Create Initiative
The create-initiative form includes an optional **Workflow** select box listing
Workflow Definitions by name. Choosing one sets `workflowDefinitionId`; leaving it
blank creates an Initiative with no linked definition.

### Workflow
Reached from the `Workflow` sidebar item. Manages **Workflow Definitions**
(blueprints): a list on the left (name + last-updated) and an editor on the right.
Leaders can **create**, **modify**, and **delete** definitions. The editor edits:

- **Name** — display name shown in the initiative/story selectors.
- **Input** — a JSON Schema (JSON editor) describing instance parameters; it is
  what react-jsonschema-form renders in Create Story.
- **Definition** — the DSL body (text editor).

Deleting a definition still referenced by an Initiative or Story is blocked
(surfaces the `409` from the API); the user detaches references first.

### Story Detail
Opens when a Story is selected. Shows:
- Planning (Tasks, dependencies, acceptance criteria)
- Timeline
- Running Tasks
- Human Requests
- Artifacts
- Logs
- Decisions

### Task Detail
- Execution history (all attempts)
- Current Capability / Provider status
- Waiting reason
- Logs
- Produced artifacts

### Attention Queue
Central inbox for all Human Requests across Initiatives, sorted by priority and
waiting time. The leader resolves Decisions here without opening each Story. See
[../execution/human-requests.md](../execution/human-requests.md).

### Notifications
Transient awareness (execution completed, approval required, workflow failed,
artifact generated). Distinct from Human Requests. See
[../notifications/notifications.md](../notifications/notifications.md).

### Artifact Viewer
Renderer selected by artifact type (Markdown, slides, diagram, code, PDF, table).
See [../execution/artifacts.md](../execution/artifacts.md).

---

## State Management

| Concern | Tool |
| ------- | ---- |
| Server state / caching | TanStack Query |
| Local UI state | Zustand |
| Realtime updates | WebSocket → updates Query cache |

WebSocket messages patch the Query cache by aggregate id + sequence; REST
reconciles on reconnect.

---

## Interaction Principles

- **Command, don't CRUD:** UI actions map to business commands (`Start`,
  `Approve`, `Retry`), mirroring the API.
- **Supervision-first:** default to read/monitor; editing is secondary.
- **No engine concepts:** the UI never shows WorkflowId/RunId/Activity.

---

## Offline Behaviour

The UI remains usable during temporary connection loss; server synchronization
resumes automatically. In-flight commands surface clear pending/failed states.

---

## Performance Targets

- Board loads within 2 seconds for 100 active executions.
- Realtime updates apply without full-page refetch.

See non-functional targets in
[../observability/observability.md](../observability/observability.md).
