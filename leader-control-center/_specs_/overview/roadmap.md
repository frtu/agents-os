# Roadmap

The architecture is designed so that increasing autonomy is a **configuration
change**, not a rewrite. Each phase reuses the same domain model, execution
model, and workflow hierarchy.

---

## MVP Scope

The first version intentionally focuses on simplicity. Automation is deferred.

**In scope**

- Portfolio / Workspace (single, implicit)
- Epic management (backing Initiatives)
- Story management
- Task management (Structured planning mode)
- Manual task execution (leader explicitly starts each task)
- Temporal integration (single workflow engine)
- Capability catalog + single-provider execution
- Execution monitoring (status + progress)
- Timeline (append-only history)
- Human decisions (approve / reject / clarify / continue / abort)
- Artifact viewing
- Attention queue

**Explicitly out of scope for MVP**

- Dependency-based auto-scheduling
- Goal-Oriented planning (AI decomposition)
- Multi-provider strategies (parallel, consensus, fan-out)
- Multiple portfolios / workspaces
- Team collaboration
- Cost tracking / analytics
- Plugin ecosystem

The MVP scheduling strategy is **Manual Scheduling** — see
[../planning/scheduling.md](../planning/scheduling.md).
The MVP execution strategy is **Single Provider** — see
[../execution/execution-strategy.md](../execution/execution-strategy.md).

---

## Progressive Automation Path

Autonomy grows along two independent axes that share the same runtime.

### Scheduling autonomy

```
Manual Scheduling (MVP)
  ↓
Dependency Scheduling      # tasks start when dependencies are satisfied
  ↓
AI Planning                # AI creates, reprioritizes, launches tasks
  ↓
Autonomous Coordination    # AI coordinates across initiatives
```

### Planning autonomy

```
Structured (MVP)           # leader defines capability, deps, criteria
  ↓
AI Suggestions             # AI proposes tasks/capabilities, leader approves
  ↓
Goal-Oriented              # leader states a goal; AI planner decomposes
  ↓
Autonomous Planning        # AI plans and executes with guardrails
```

See [../planning/planning-modes.md](../planning/planning-modes.md).

---

## Future Evolution

Without changing the architecture, future versions can introduce:

- Dependency-based scheduling
- AI planning and dynamic task creation
- Multi-provider execution strategies (parallel, consensus, loop, fan-out)
- Additional workflow engines via adapters (e.g. LangGraph)
- Multiple portfolios / workspaces
- Team collaboration and role-based permissions
- Notifications across channels (Slack, email)
- Plugin ecosystem and MCP integrations
- Analytics and cost tracking
- Execution replay from the event log

---

## Definition of Done per Phase

A phase is complete when:

1. Its capabilities exist as **explicit** operations in the API.
2. Business rules are testable **without** requiring Temporal (see
   [../observability/observability.md](../observability/observability.md) and
   NFRs in this folder's siblings).
3. No planning or runtime schema change is required to enable the next phase —
   only new strategies/adapters/config.
