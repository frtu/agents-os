# Workflow Engine

Workflow engines **execute** work. They do not own Epics, Stories, Planning, or
Priorities. They only execute Tasks and their Capabilities.

The initial target engine is **Temporal**. Future engines integrate through the
same adapter port.

---

## Boundary Rule

Engine concepts never leak past the Workflow Engine Context.

The backend exposes:
```
StoryExecution · TaskExecution · CapabilityExecution · ProviderExecution
Timeline · Decision · HumanRequest
```

The backend never exposes:
```
WorkflowId · RunId · Activity · TaskQueue
```

See [../domain/bounded-contexts.md](../domain/bounded-contexts.md).

---

## Workflow Hierarchy

The execution hierarchy maps onto workflows:

```
Story Workflow
  ↓
Task Workflow
  ↓
Capability Workflow
  ↓
Provider Activity
```

### Story Workflow
- coordinates Task Workflows via the active Scheduling Strategy
- aggregates Artifacts and Story status
- MVP only observes manual execution; future versions auto-schedule Tasks

### Task Workflow
- runs the Task's Capability via an Execution Strategy
- waits for Decisions (signals)
- retries failures per strategy
- produces Artifacts

### Capability Workflow
- executes the chosen Execution Strategy
- coordinates one or more Provider Activities

### Provider Activity
- the concrete Provider call (LLM, MCP tool, human task, etc.)
- the only place engine/provider specifics live

---

## Signals (commands → engine)

External commands become workflow signals:

```
Approve · Reject · Clarify · Continue · Abort · Cancel · Retry · SelectOption
```

Applying a Decision (see
[../execution/human-requests.md](../execution/human-requests.md)) delivers a
signal to the waiting Task/Capability Workflow.

---

## Queries (engine → backend)

The backend may query workflows for live state:

```
Current Step · Current Capability/Provider · Waiting Reason · Progress · Estimated Completion
```

---

## Events (engine → timeline)

The engine emits domain events; the Workflow Engine Context persists them as
Runtime events, which project into the Timeline:

```
ExecutionStarted · CapabilityStarted · ProviderFailed · RetryScheduled
DecisionRequested · DecisionReceived · ArtifactProduced · ExecutionCompleted · ExecutionFailed
```

See [../domain/event-model.md](../domain/event-model.md).

---

## Adapter Port (Ports & Adapters)

Business logic depends only on the `WorkflowEngine` interface:

```
WorkflowEngine
  startStory(storyExecution)
  startTask(taskExecution)
  signal(executionId, signal, payload)
  query(executionId, query) → state
  cancel(executionId)
```

```
Application → WorkflowEngine (port) → Temporal Adapter → Temporal
                                    ↘ (future) LangGraph Adapter → LangGraph
```

Adding an engine adds an adapter; no business logic changes. See
[../backend/architecture.md](../backend/architecture.md).

---

## Scheduling Delegation

Scheduling is delegated to a strategy the Story Workflow consults; the hierarchy
is unchanged across strategies.

```
Current: ManualSchedulingStrategy
Future:  DependencySchedulingStrategy · AIPlanningStrategy
```

See [../planning/scheduling.md](../planning/scheduling.md).

---

## Testability

Business rules (state machines, strategy decisions, scheduling) must be testable
**without** a running Temporal instance — the adapter is mockable behind the
port. See [../observability/observability.md](../observability/observability.md).
