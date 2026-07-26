# Execution Strategy

An Execution Strategy determines **how** a Capability is executed across
Providers. Separating strategy from provider enables progressively more advanced
orchestration without changing planning.

```
Capability → Execution Strategy → Provider(s) → Provider Execution(s)
```

Exactly one Execution Strategy runs per Capability Execution.

---

## Contract

```
ExecutionStrategy
  run(capabilityExecution, providers, context) → CapabilityResult
```

A strategy decides:
- which Providers to invoke and in what shape (one, many, sequenced)
- how to interpret Provider success/failure
- when to raise a Human Request
- what the final Capability result is

---

## Supported Strategies

### Single Provider (MVP)
```
Capability → Claude
```
One Provider Execution. Success = provider success.

### Retry
```
Claude → Retry → Retry → Completed
```
Re-invoke on failure up to a limit; each attempt is a new Provider Execution.

### Parallel
```
Capability → { Claude, GPT, Gemini }
```
Invoke several Providers concurrently; return the first/best success.

### Consensus
```
{ Claude, GPT, Gemini } → Merge → Result
```
Invoke several Providers and merge their outputs into one result.

### Human Review
```
LLM → Human Approval → Continue
```
Produce a candidate, then raise a Human Request; the Decision gates continuation.
See [human-requests.md](./human-requests.md).

### Pipeline
```
Research → Write → Review → Publish
```
Sequence Capabilities/Providers, feeding each output into the next.

### Loop
```
Generate → Evaluate → Improve → (Satisfied?)
```
Iterate until an acceptance condition is met or a limit is reached.

### Fan-Out
```
Research → { Region A, Region B, Region C } → Merge
```
Split into parallel sub-executions, then merge results.

---

## Strategy vs Scheduling

- **Scheduling Strategy** decides *when a Task starts* (see
  [../planning/scheduling.md](../planning/scheduling.md)).
- **Execution Strategy** decides *how a Capability runs* once a Task Execution is
  underway.

They are orthogonal and evolve independently.

---

## Selection

- **MVP:** every Capability Execution uses **Single Provider**.
- **Future:** strategy is chosen from Capability configuration, Portfolio
  defaults, or (eventually) the AI Planner. Selection is configuration, not code.

---

## Invariants

1. Execution Strategies are implementation details; planning never references a
   strategy.
2. A Provider failure is interpreted by the strategy, not assumed to be a
   Capability failure.
3. Any strategy may raise Human Requests; runtime pauses until the Decision is
   applied.
4. Adding a new strategy must not require changes to the execution hierarchy.
