# Application Services & Commands

The application layer exposes **use cases** as command and query handlers. It
orchestrates domain aggregates, the Catalog, and the Workflow Engine port. It
contains no HTTP or persistence details (those live in the API and infra layers).

```
API → Command/Query Handler → Domain Aggregate → Event → Projection
                            ↘ WorkflowEngine port (for runtime commands)
```

---

## Command Handlers

Commands express intent and are the only way to change state.

### Planning
| Command | Aggregate | Emits |
| ------- | --------- | ----- |
| `CreateInitiative` | Initiative | `InitiativeCreated` |
| `CreateEpic` | Initiative | `EpicCreated` |
| `CreateStory` | Story | `StoryCreated` |
| `CreateTask` | Story | `TaskCreated` |
| `UpdateTask` | Task | `TaskUpdated` |
| `MarkTaskReady` | Task | `TaskReady` |
| `CancelTask` | Task | `TaskCancelled` |

`CreateInitiative` accepts an optional `workflowDefinitionId`. `CreateStory`
accepts an optional `workflowDefinitionId` + `templateInput`; when present the
handler validates `templateInput` against the definition's `input` JSON Schema
before emitting `StoryCreated`.

### Workflow Definitions
Blueprints are edited directly (not command/CRUD-hybrid like Planning). They are
Portfolio-scoped catalog data, distinct from the Temporal Workflow Engine.

| Command | Aggregate | Emits |
| ------- | --------- | ----- |
| `CreateWorkflowDefinition` | WorkflowDefinition | `WorkflowDefinitionCreated` |
| `UpdateWorkflowDefinition` | WorkflowDefinition | `WorkflowDefinitionUpdated` |
| `DeleteWorkflowDefinition` | WorkflowDefinition | `WorkflowDefinitionDeleted` |

`DeleteWorkflowDefinition` fails (`409`) while any Initiative or Story references
the definition.

### Runtime
| Command | Effect | Emits |
| ------- | ------ | ----- |
| `StartStory` | create Story Execution, start Story Workflow | `StoryExecutionCreated`, `StoryStarted` |
| `StartTask` | create Task Execution, start Task Workflow | `TaskStarted` |
| `CancelExecution` | signal engine cancel | `TaskExecutionCancelled` |
| `RetryExecution` | new execution instance | `RetryScheduled`, `TaskStarted` |

### Decisions
| Command | Effect | Emits |
| ------- | ------ | ----- |
| `ApproveDecision` | signal engine `Approve` | `DecisionSubmitted`, `DecisionApplied` |
| `RejectDecision` | signal `Reject` | `DecisionSubmitted`, `DecisionApplied` |
| `ClarifyDecision` | signal `Clarify` (+ payload) | `DecisionSubmitted`, `DecisionApplied` |
| `ContinueExecution` | signal `Continue` | `DecisionApplied` |
| `AbortExecution` | signal `Abort` | `DecisionApplied`, `TaskExecutionCancelled` |
| `SelectOption` | signal `SelectOption` | `DecisionApplied` |

Runtime commands are translated into workflow **signals** via the WorkflowEngine
port — see [../workflow-engine/workflow-engine.md](../workflow-engine/workflow-engine.md).

---

## Query Handlers (read models)

Queries never touch aggregates; they read projections.

| Query | Returns |
| ----- | ------- |
| `GetInitiativeBoard` | Kanban view (Stories by column) |
| `GetStoryExecution` | live status + progress |
| `GetTimeline` | append-only events for an execution |
| `GetArtifacts` | artifacts for a Story/Task |
| `GetAttentionQueue` | cross-initiative human requests + failures |
| `ListWorkflowDefinitions` | Workflow Definition blueprints (name + metadata) |
| `GetWorkflowDefinition` | one definition (input JSON Schema + DSL body) |

See [../domain/event-model.md](../domain/event-model.md) for projections.

---

## Handler Responsibilities

1. **Validate** the command against aggregate invariants (e.g. only `Ready` Tasks
   start).
2. **Resolve** Catalog references (Capability → supported Providers).
3. **Emit** events (source of truth).
4. **Delegate** runtime effects to the WorkflowEngine port.
5. **Never** embed engine/provider specifics — those live behind ports.

---

## Idempotency & Concurrency

- Commands carry a client-supplied idempotency key where retries are possible
  (Start/Retry).
- Aggregates use optimistic concurrency (`version`); conflicting writes return
  `409` (see [../api/rest-api.md](../api/rest-api.md)).
- Decision application is idempotent: re-applying the same Decision is a no-op.
