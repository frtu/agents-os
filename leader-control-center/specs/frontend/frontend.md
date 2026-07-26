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

## Views

### Initiative Board
Collapsible drawers per Initiative; Stories as cards in columns; progress and
attention badges.

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
