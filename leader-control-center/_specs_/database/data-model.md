# Data Model

PostgreSQL schema backing the domain. Planning tables hold stable intent; Runtime
tables hold disposable execution; the event log is the append-only source of
truth for runtime projections.

Conventions: every row has `id (uuid)`, `created_at`, `updated_at`, and a
`version` for optimistic locking unless noted.

---

## Catalog

### workspace / portfolio
```
workspace(id, name, created_at)
portfolio(id, workspace_id, name, default_ai_config jsonb)
```

### capability
```
capability(id, portfolio_id, name, description,
           inputs jsonb, outputs jsonb, version, status)
```

### provider
```
provider(id, portfolio_id, name, type,            -- llm|mcp|human|activity
         supported_capabilities uuid[],
         config jsonb, credential_ref, status)
```

### workflow_definition
A reusable **blueprint** (authoring-time DSL) that governs how work is created:
`input` is a JSON Schema describing the parameters an instance requires;
`definition` is the DSL text realizing the workflow. It is *not* the Temporal
Workflow Engine (see [../workflow-engine/workflow-engine.md](../workflow-engine/workflow-engine.md)),
which executes runtime work behind a port — a Workflow Definition is stored
Planning-catalog intent that seeds Initiatives and Stories.
```
workflow_definition(id, portfolio_id, name,
                    input jsonb,          -- JSON Schema for instance parameters
                    definition text,      -- DSL body
                    created_at, updated_at, version)
```

---

## Planning (immutable intent)

### initiative
```
initiative(id, portfolio_id, title, description, status,  -- Draft|Ready|Archived
           workflow_definition_id)                        -- nullable FK, optional blueprint
```

### epic
```
epic(id, initiative_id, title, description, status)       -- Draft|Ready|Archived
```

### story
```
story(id, epic_id, title, description, priority, status,  -- Draft|Ready|Archived
      workflow_definition_id,                             -- nullable FK, set when created from template
      template_input jsonb)                               -- instance params captured from the definition's JSON Schema
```

### task
```
task(id, story_id, name, planning_mode,                   -- Structured|GoalOriented
     capability_id, capability_version,                   -- Structured
     goal, success_criteria jsonb,                        -- GoalOriented
     status,                                              -- Draft|Ready|Cancelled
     "order")
```

### dependency
```
dependency(task_id, depends_on_task_id)                   -- DAG within a story
```

### acceptance_criteria
```
acceptance_criteria(id, story_id, task_id, description)   -- one of story/task set
```

---

## Runtime (disposable execution)

### story_execution
```
story_execution(id, story_id, status, started_at, completed_at)
                                    -- Created|Running|Waiting|Completed|Cancelled|Failed
```

### task_execution
```
task_execution(id, story_execution_id, task_id, status, started_at, completed_at)
                                    -- Created|Running|WaitingDecision|Completed|Failed|Cancelled
```

### capability_execution
```
capability_execution(id, task_execution_id, capability_id,
                     strategy, status)   -- Pending|Running|Waiting|Completed|Failed
```

### provider_execution
```
provider_execution(id, capability_execution_id, provider_id,
                   status, attempt, started_at, ended_at, result jsonb)
                                    -- Scheduled|Running|Succeeded|Failed|Cancelled
```

---

## Human Interaction

### human_request
```
human_request(id, execution_id, initiative_id, type, prompt,
              options jsonb, priority, status, created_at)
                                    -- Created|Visible|Acknowledged|Resolved|Closed
```

### decision
```
decision(id, human_request_id, decision, selected_option,
         comment, user_id, created_at)
                                    -- immutable
```

---

## Artifacts

### artifact
```
artifact(id, execution_id, type, version, owner, created_by,
         location, metadata jsonb, parent_artifact_id, created_at)
```
Immutable rows; a new version is a new row linked via `parent_artifact_id`.

---

## Events & Projections

### event (append-only source of truth)
```
event(id, type, category, aggregate_id, initiative_id,
      payload jsonb, actor, occurred_at, sequence)
```
- Never updated or deleted.
- `sequence` is monotonic per `aggregate_id`.

### projections (rebuildable from events)
```
timeline_entry(id, execution_id, type, payload jsonb, occurred_at)
attention_item(id, initiative_id, execution_id, type, priority, waiting_since)
board_view(...)          -- materialized Kanban per initiative
metrics(...)             -- durations, success rates
notification(id, user_id, type, payload jsonb, read, created_at)
```

Projections are derived; the `event` table is authoritative. See
[../domain/event-model.md](../domain/event-model.md).

---

## Identity & Access

```
app_user(id, portfolio_id, name, email, role)
credential(id, portfolio_id, name, secret_ref)   -- secrets stored externally
```

See [../auth/auth.md](../auth/auth.md) and
[../permissions/permissions.md](../permissions/permissions.md).

---

## Key Relationships & Constraints

- `task.capability_id` → `capability.id` (Structured tasks; enforced at command
  time).
- `initiative.workflow_definition_id` and `story.workflow_definition_id` →
  `workflow_definition.id` (both nullable; a Workflow Definition is Portfolio-level
  catalog intent, so Planning may reference it just like `capability_id`).
- `story.template_input` must validate against the referenced
  `workflow_definition.input` JSON Schema when `workflow_definition_id` is set.
- `dependency` forms a DAG within a Story (no cycles).
- Runtime tables reference Planning by id but Planning has **no** FK to Runtime
  (Planning never depends on Runtime).
- `event`, `decision`, and `artifact` rows are immutable.
- Optimistic locking via `version` on all mutable Planning/Runtime aggregates.
