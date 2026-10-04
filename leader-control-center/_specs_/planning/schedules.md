# Schedules (time-triggered Stories)

A **Schedule** creates and starts a new Story from a Workflow Definition at
planned times: once, on a fixed interval, or on a cron expression. It answers
*when should this recurring work happen again*. It does not decide which Task
runs next inside a Story; that is the [Scheduling Strategy](./scheduling.md).

```
Schedule "Weekly risk review"  ·  every Monday 09:00 Europe/Paris
   │ occurrence 2026-10-05T09:00+02:00
   ▼
CreateStory(workflowDefinitionId, templateInput)  →  StartStory
   │
   ▼
Board (Initiative "Platform Modernization")
   [Risk review · 2026-10-05]  Completed
   [Risk review · 2026-10-12]  Running
```

Design reference: OpenClaw's Gateway automations (`src/cron`, docs
`automation/cron-jobs/*`). We reuse their scheduler semantics (schedule kinds,
catch-up, one-in-flight, run history, auto-disable on repeated failure, confirm
in plain words at creation). Their payload/delivery/channel model is not
reused; here those roles belong to Capability, Provider, and Notifications.

---

## Decisions

| # | Decision | Rationale |
| - | -------- | --------- |
| D1 | **Each occurrence creates a new Story** from a Workflow Definition + fixed `templateInput`, then starts it. | Planning stays immutable: a Completed Story is never re-opened. Each occurrence gets its own board card, history, and artifacts. |
| D2 | **Timer behind a `SchedulerPort`** with two adapters: in-process (SQLite + asyncio) and Temporal Schedules. | Works today with the SimulationEngine; durable with Temporal. Business code never sees a timer implementation. |
| D3 | **Occurrences auto-start.** Approval happens once, at creation: the leader confirms a plain-language sentence and may trigger a test run. | Human supervision during the run still comes from Human Requests. A run that fails visibly is safer than one waiting unnoticed for a start approval. |
| D4 | **Overlap policy is chosen per Schedule at creation**; default `Skip`. | A Story paused on a Human Request must not silently pile up duplicates. Teams that need every occurrence can pick `BufferOne` or `AllowParallel`. |
| D5 | **The application decides overlap and catch-up**; adapters only deliver ticks. | One engine-independent implementation of the rules. Adapters stay thin and behave the same way. |
| D6 | **A Schedule belongs to one Initiative**; its Stories land in that Initiative's Epic. | Fits the existing Story model unchanged; the board shows where recurring work lives. |
| D7 | **Auto-archive per Schedule:** keep the last N Completed scheduled Stories on the board (default 5). | Prevents one-card-per-occurrence from flooding the board. History and artifacts are kept. |
| D8 | **Schedule lives in the Planning context.** | It is intent about *when* work happens; it drives Runtime through the same commands a leader uses. No new bounded context. |
| D9 | **Runtime-aware rules live in an application process manager** (`ScheduleService`), not in the Schedule aggregate. | Planning never references runtime IDs or depends on execution status ([bounded-contexts](../domain/bounded-contexts.md)). The service reads Runtime projections and reacts to Runtime events, and the aggregate stores Planning IDs only. |

---

## Concepts

| Term | Definition |
| ---- | ---------- |
| **Schedule** | Planning intent: *create Story X from definition D in Initiative I at times T*. Owned by an Initiative. |
| **Schedule Spec** | The time rule: `Once`, `Interval`, or `Cron`. |
| **Occurrence** | One planned point in time (`scheduledFor`) produced by the Spec. |
| **Schedule Run** | The permanent record of what happened to one Occurrence: started a Story, skipped, missed, or failed to start. |
| **Overlap Policy** | What to do when an Occurrence comes due while an earlier run of the same Schedule is still active. |
| **Catch-up Window** | How late an Occurrence may still start (after downtime) before it is recorded as Missed. |

---

## Schedule Model

```
Schedule {
  id
  initiativeId                 # Stories land in this Initiative's Epic
  name                         # "Weekly risk review"
  workflowDefinitionId         # required (D1)
  templateInput                # validated against the definition's input schema
  storyTitleTemplate           # default "{name} · {date}"  ({name} {date} {datetime} {n})
  spec        : ScheduleSpec
  overlapPolicy: Skip | BufferOne | AllowParallel      # default Skip (D4)
  catchUpWindow: duration      # default PT1H
  keepCompleted: int           # default 5; older Completed scheduled Stories are archived (D7)
  status      : Active | Paused | Completed | Archived
  pauseReason : Manual | ConsecutiveFailures | InvalidTemplate | null
  createdBy                    # user who confirmed the Schedule
  # projection fields (read-only)
  nextOccurrenceAt
  lastRun { scheduledFor, status, storyId }
  consecutiveFailures
}
```

### Schedule Spec

| Kind | Fields | Example |
| ---- | ------ | ------- |
| `Once` | `at` (ISO 8601 with offset) | `2026-11-02T08:00:00+01:00` |
| `Interval` | `every` (ISO 8601 duration, ≥ `PT5M`), `anchor?` | `P1D` from `2026-10-05T07:00Z` |
| `Cron` | `expression` (5-field), `timezone` (IANA, required) | `0 9 * * MON`, `Europe/Paris` |

Rules:
- Timezone is required for `Cron`, so behavior never depends on the server's
  timezone. DST: a skipped local time fires at the next valid time; a repeated
  local time fires once.
- Cron uses standard OR semantics when both day-of-month and day-of-week are
  set (as noted in OpenClaw's docs). The preview (below) makes this visible.
- Minimum interval `PT5M`. Each fire creates a Story, so tighter loops do not
  make sense for leader-level work.
- Out of scope for v1 (see Future): event triggers, condition watchers, pacing,
  and jitter/stagger.

---

## Lifecycles

### Schedule

```
          create (confirmed)
               │
               ▼
 ┌────────▶ Active ──── Once fired ────▶ Completed
 │            │  ▲
 │     pause  │  │ resume
 │            ▼  │
 │          Paused
 │            │
 └── (any) ── archive ──▶ Archived      (terminal; history kept)
```

- **Paused** stops new Occurrences. Story Executions already started keep running.
- **Auto-pause:** after **3 consecutive failed runs**, or when `templateInput`
  no longer validates against the (edited) definition. The Schedule moves to
  Paused with a `pauseReason`, and a Notification is raised (see Failure Handling).
- **Resume** recomputes `nextOccurrenceAt` from *now*. Occurrences that passed
  while Paused are not caught up.
- Editing `spec`, `templateInput`, `overlapPolicy` or `catchUpWindow` is allowed
  in Active or Paused. It starts a new scheduling decision, and pending
  buffered Occurrences are dropped (recorded as Skipped).

### Schedule Run

```
Due ──▶ Started            (Story created + StartStory issued)
   ├──▶ Buffered ──▶ Started | Skipped
   ├──▶ Skipped            (overlap policy, or edit/pause dropped it)
   ├──▶ Missed             (later than catchUpWindow)
   └──▶ FailedToStart      (template invalid, Initiative archived, engine error)
```

A Started run's **outcome** mirrors its Story Execution's terminal state
(`Completed | Failed | Cancelled`) once known. It is a read-model projection
that joins the Story's latest execution. Schedule Run itself stores only the
`storyId` (D9).

---

## Firing Algorithm (application layer)

The adapter delivers `OccurrenceDue(scheduleId, scheduledFor, firedAt)`. The
`ScheduleService` (application-layer process manager, D9) handles it. It may
read Runtime projections; the Schedule aggregate never does.

```
1. Load the Schedule. If it is not Active → record Skipped (reason: NotActive). Stop.
2. If firedAt − scheduledFor > catchUpWindow → record Missed. Stop.
3. Idempotency: if a Schedule Run exists for (scheduleId, scheduledFor) → stop.
4. active = Story Executions (Runtime projection) of Stories with this
   scheduleId, in Created|Running|Waiting
   if active is non-empty:
     Skip          → record Skipped (reason: PreviousRunActive). Stop.
     BufferOne     → record Buffered; replace any earlier Buffered run
                     (the replaced run becomes Skipped). Stop.
     AllowParallel → continue.
5. CreateStory(initiative epic, title from storyTitleTemplate,
               workflowDefinitionId, templateInput,
               origin = { scheduleId, scheduledFor })
   StartStory(story)
   → record Started { storyId }
6. On error in 5 → record FailedToStart; consecutiveFailures += 1.
```

- **BufferOne release:** on `StoryExecutionCompleted|Failed|Cancelled` for a
  Story created by the Schedule, the service starts the Buffered run (steps 5–6)
  if the Schedule is still Active.
- **Catch-up after downtime:** adapters deliver missed Occurrences with their
  original `scheduledFor`. Only the latest Occurrence inside the window starts;
  older ones are recorded Missed. This mirrors OpenClaw's coalescing and
  Temporal's `catchupWindow`.
- **Exactly one Story per Occurrence:** `(scheduleId, scheduledFor)` is a
  unique key on Schedule Run, and it is the idempotency key for `CreateStory`.
  A duplicate tick (adapter retry, restart, two adapters) is a no-op.
- **Auto-archive (D7):** on `StoryExecutionCompleted` for a scheduled Story,
  archive (Story planning state → `Archived`) the oldest Completed Stories of
  that Schedule beyond `keepCompleted`. Failed or Cancelled Stories are never
  auto-archived; they stay visible until a leader handles them. Archived Stories
  remain reachable from the Schedule's run history.
- **Failure counting:** `FailedToStart` and a Started run whose Story Execution
  ends `Failed` count as failures. `Completed` resets the counter. `Cancelled`
  (a human decision) and `Skipped`/`Missed` neither count nor reset.

---

## Creation Flow (approval happens here, D3)

```
1. Leader fills the Schedule form (definition + templateInput + spec + overlap).
2. POST /schedules/preview → plain sentence + next 5 occurrences (in the spec's
   timezone and the viewer's local time).
   "Every Monday at 09:00 (Europe/Paris), create and start
    'Weekly risk review · {date}' in Platform Modernization.
    If the previous run is still active, skip."
3. Leader confirms → CreateSchedule (status Active).
4. Optional "Run once now" → TriggerSchedule: a real, out-of-band Occurrence
   (scheduledFor = now). Its Story appears on the board immediately.
   It does not move the next natural Occurrence.
```

Following OpenClaw, Schedules are created **Active**, never "disabled pending
approval". A disabled Schedule waiting for a confirmation nobody sees fails
silently. The confirmation in step 3 is the approval.

---

## Failure Handling & Supervision

| Situation | Effect |
| --------- | ------ |
| Run fails (FailedToStart, or Story Execution Failed) | Notification `ScheduleRunFailed` (links the Story). The failed execution also appears in the Attention Queue as any failure does. |
| 3 consecutive failures | Auto-pause (`ConsecutiveFailures`). Notification `SchedulePaused` with the reason and a Resume action. |
| Definition edited, `templateInput` now invalid | Auto-pause (`InvalidTemplate`) at the next Occurrence. The run is recorded FailedToStart. |
| Initiative archived | All its Schedules are archived. |
| Human Request inside a scheduled Story | Normal behavior: the Story waits. The Overlap Policy decides what the next Occurrence does. |

There are no Schedule-level retries. Provider-level retries belong to the
[Execution Strategy](../execution/execution-strategy.md), and a leader can
retry the execution manually.

---

## Identity & Permissions

- Creating, editing, pausing, resuming, triggering and archiving a Schedule are
  **protected operations** (Leader role), like `StartStory`.
- Each Occurrence's `CreateStory` and `StartStory` run as the system actor
  `scheduler` **on behalf of** `createdBy`. Events record both
  (`actor: system:scheduler`, `onBehalfOf: <userId>`), so audit shows who
  authorized the recurring work. This is the "service accounts for scheduled
  runs" item in [../auth/auth.md](../auth/auth.md).

---

## SchedulerPort (engine boundary)

```
SchedulerPort
  register(schedule)            # create or replace the timer for a Schedule
  pause(scheduleId)
  resume(scheduleId)
  remove(scheduleId)
  nextOccurrences(spec, n, from) → [datetime]   # pure; also used by /preview
callback (application side):
  ScheduleService.on_occurrence_due(scheduleId, scheduledFor, firedAt)
```

The port carries domain types only (`Schedule`, `ScheduleSpec`). Temporal
schedule IDs, actions and policies stay inside the adapter, per the rule in
[../workflow-engine/workflow-engine.md](../workflow-engine/workflow-engine.md).
`TriggerSchedule` does not go through the port: the application calls
`on_occurrence_due` directly with `scheduledFor = now`.

### In-process adapter (default; SimulationEngine)

- Stores `next_occurrence_at` per Schedule in SQLite. An asyncio loop in the app
  lifespan (next to the simulation tick) wakes at the earliest due time
  (capped at 30 s) and delivers every due Occurrence.
- On startup, it delivers missed Occurrences with their original
  `scheduledFor`. The application applies the catch-up window.
- Cron parsing and next-time computation use a library (`croniter`),
  wrapped so a library swap does not affect the port.

### Temporal adapter

- One Temporal Schedule per Schedule (`ScheduleClient`). The internal ID is
  derived from `scheduleId` and never leaves the adapter.
- `Cron` → `ScheduleSpec(cron_expressions, time_zone_name)`. `Interval` →
  `ScheduleIntervalSpec(every, offset)`. `Once` → a `ScheduleCalendarSpec`
  matching that single date/time (year included) plus
  `ScheduleState(limited_actions=True, remaining_actions=1)`.
- Action: start a short `OccurrenceWorkflow` whose single activity calls
  `ScheduleService.on_occurrence_due(scheduleId, scheduledFor, firedAt)`.
  Temporal's overlap policy is `ALLOW_ALL` and its catch-up window matches the
  Schedule's; the business rules stay in the application (D5).
- `pause` / `resume` / `remove` map onto the Temporal Schedule handle.
- Contract and helpers: [../../backend/dependencies.md](../../backend/dependencies.md)
  (`CreateSchedule`, `PatchSchedule`, `DescribeSchedule`, `ListScheduleMatchingTimes`).

---

## Commands & Events

| Command | Effect | Emits |
| ------- | ------ | ----- |
| `CreateSchedule` | validate definition + templateInput + spec; `register` | `ScheduleCreated` |
| `UpdateSchedule` | revalidate; `register` (replace); drop Buffered | `ScheduleUpdated` |
| `PauseSchedule` / `ResumeSchedule` | `pause` / `resume` | `SchedulePaused` / `ScheduleResumed` |
| `TriggerSchedule` | out-of-band Occurrence now | `ScheduleOccurrenceDue`, then as below |
| `ArchiveSchedule` | `remove` | `ScheduleArchived` |
| (internal) `OccurrenceDue` | firing algorithm | `ScheduleRunStarted` · `ScheduleRunBuffered` · `ScheduleRunSkipped` · `ScheduleRunMissed` · `ScheduleRunFailedToStart` · `SchedulePaused(auto)` · `ScheduleCompleted` |

Schedule events are in the **Planning** category (aggregate = Schedule). The
Story and runtime events they trigger (`StoryCreated`, `StoryStarted`, …) carry
`origin.scheduleId` in their payload.

---

## API (`/api/v1`)

```
GET    /schedules?initiativeId=          list (status, spec summary, nextOccurrenceAt, lastRun)
GET    /schedules/{id}                   detail + next 5 occurrences
GET    /schedules/{id}/runs              Schedule Run history (newest first, paginated)
POST   /schedules/preview                { spec, overlapPolicy, ... } → { sentence, nextOccurrences[] }
POST   /schedules                        CreateSchedule
PATCH  /schedules/{id}                   UpdateSchedule   (If-Match: version)
POST   /schedules/{id}/pause             PauseSchedule
POST   /schedules/{id}/resume            ResumeSchedule
POST   /schedules/{id}/trigger           TriggerSchedule ("Run now")
POST   /schedules/{id}/archive           ArchiveSchedule
```

Request example:

```json
{
  "initiativeId": "ini_123",
  "name": "Weekly risk review",
  "workflowDefinitionId": "wd_risk",
  "templateInput": { "scope": "platform", "depth": "summary" },
  "storyTitleTemplate": "{name} · {date}",
  "spec": { "kind": "Cron", "expression": "0 9 * * MON", "timezone": "Europe/Paris" },
  "overlapPolicy": "Skip",
  "catchUpWindow": "PT1H",
  "keepCompleted": 5
}
```

- `422`: invalid spec, timezone, `templateInput` (schema violation), or
  interval below `PT5M`.
- `409`: commands on an Archived Schedule; `DELETE /workflow-definitions/{id}`
  while a non-archived Schedule references it.
- Realtime: `ScheduleUpdated` (status/next occurrence) and
  `ScheduleRunRecorded` (new Schedule Run), via the existing stream; clients
  invalidate queries. See [../api/realtime.md](../api/realtime.md).

---

## Data Model

```
schedule(id, initiative_id, name,
         workflow_definition_id,              -- FK, required
         template_input jsonb,
         story_title_template,
         spec jsonb,                           -- {kind, at | every+anchor | expression+timezone}
         overlap_policy,                       -- Skip|BufferOne|AllowParallel
         catch_up_window_seconds,
         keep_completed,                       -- auto-archive threshold (D7)
         status, pause_reason,                 -- Active|Paused|Completed|Archived
         consecutive_failures,
         next_occurrence_at,                   -- in-process adapter cursor / projection
         created_by, created_at, updated_at, version)

schedule_run(id, schedule_id, scheduled_for, fired_at,
             status,                           -- Started|Buffered|Skipped|Missed|FailedToStart
             reason,                           -- PreviousRunActive|NotActive|Edited|...
             story_id,                         -- when Started (Planning id only, D9)
             error,
             unique (schedule_id, scheduled_for))

story(+ schedule_id nullable, + scheduled_for nullable)   -- origin, for the board badge
```

SQLite MVP: stored as JSON documents like the other aggregates (see
[../../backend/storage.md](../../backend/storage.md)). The
`(schedule_id, scheduled_for)` uniqueness is enforced in the store.

---

## Frontend

- **Schedules** sidebar item: a list grouped by Initiative (name, plain-language
  spec, next occurrence, last-run status chip, status). Actions: Pause/Resume,
  Run now, Edit, Archive.
- **Create/Edit drawer:** Initiative, name, Workflow Definition select, its
  `input` schema rendered with react-jsonschema-form (as in Create Story), a
  spec picker (Once / Interval / Cron with timezone), an Overlap Policy select
  (default *Skip if previous run is active*), the live preview sentence + next 5
  occurrences, a **Run once now** checkbox, and Confirm.
- **Board:** Stories created by a Schedule show a clock badge that links to the
  Schedule. The card title already carries the occurrence date. Only the last
  `keepCompleted` Completed runs stay on the board (D7).
- The Create/Edit drawer also has **Keep last N completed on board** (default 5).
- **Schedule detail:** run history (scheduledFor, status/reason, link to Story,
  execution outcome).

---

## Testing

- The firing algorithm is pure application logic, testable with an injected
  clock and a fake `SchedulerPort` (no Temporal), per the
  [workflow-engine testability rule](../workflow-engine/workflow-engine.md#testability).
- Cases: each Overlap Policy; catch-up inside/outside the window; duplicate
  tick idempotency; auto-pause at 3 failures; reset on Completed; Once → Completed;
  edit drops Buffered; DST forward/back for Cron; auto-archive keeps exactly
  `keepCompleted` and never archives Failed/Cancelled.
- Temporal adapter: integration test against the local stack (`../start.sh`),
  using `scripts/temporal-api.sh call DescribeSchedule` to inspect.

---

## Future (not in v1)

- **Event triggers:** fire on an external event or webhook instead of time
  (OpenClaw `on-exit` / `stream` / hooks).
- **Condition watchers:** a cheap check runs on schedule, and the Story is
  created only when it reports `fire: true` (OpenClaw trigger scripts).
- **Pacing:** a run proposes its own next check within min/max bounds.
- **Promotion:** offer "make this a Schedule" when a leader repeatedly creates
  the same templated Story.
- **Portfolio-level Schedules** for cross-initiative work (needs a home for
  their Stories).
- **Automation context:** move Schedule into its own bounded context if event
  triggers, watchers and pacing grow it beyond Planning.
- **Stagger/jitter** for many Schedules due at the top of the hour.

