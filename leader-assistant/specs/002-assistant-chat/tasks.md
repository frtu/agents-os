# Tasks: Product Owner Chat

**Feature ID:** `002-assistant-chat` · **Plan:** [`plan.md`](plan.md)
**Last Updated:** 2026-08-16

> Ordered build steps derived from [`spec.md`](spec.md) and [`plan.md`](plan.md). Each
> references the FR/AC or invariant it satisfies. `[P]` = parallelizable (no shared files,
> no dependency). This feature realizes feature 001 tasks **T071–T074** concretely.

## Legend

- `[ ]` pending · `[x]` done · `[P]` parallelizable
- Refs: `FR-n`/`AC-n` from [`spec.md`](spec.md); invariants from [`20-testing`](../20-testing.md); `[[NN-name]]` specs.

## Setup

- [x] T001 Confirm `claude-agent-sdk` is installed and importable under `uv`; add a tiny
  smoke import test. (plan Technical Context)
- [x] T002 [P] Add pydantic models to `app/models.py`: `ChatRequest`, `ChatAnswer`,
  `ChatDelta` (reuse `Citation`, `Plan`). (FR-1; plan Interfaces)

## Persona

- [x] T010 Product Owner prompt assembler: build the system prompt from
  `memory/constitution.md` + curated numbered specs (00, 01, 07, 09, 13, 14); expose as a
  pure function. (FR-8; realizes 001 T003)
- [x] T011 [P] Persona guardrails in the prompt: answer from the workspace with citations,
  plan-first for consequential work, state assumptions, never write `vault/raw/`. (FR-2, FR-5, FR-11, FR-12)

## Core — conversation store (durable, resumable)

- [x] T015 Conversation store: `<workspace>/sessions/<conversation_id>.md` — one file per
  conversation; `load(conversation_id)` reconstructs turn history + any `pending-plan`;
  `append_turn(...)` is append-only for turns. Resumable after restart. (FR-3, FR-7, FR-13; [[06-conversations]] AC1)
- [x] T016 Pending-plan storage: set/clear the `pending-plan` frontmatter block (the one
  mutable field) when a plan is proposed / approved. (FR-5, FR-13; D2)

## Core — capability layer (the parity boundary)

- [x] T020 `capabilities.ask(workspace, message, conversation_id, approve=False) -> ChatAnswer`:
  load/create the conversation, resolve workspace, load persona, run the agent, append the turn,
  return reply + `conversation_id` + citations (+ `pending_plan`). (FR-1, FR-2, FR-8, FR-13; P9)
- [x] T021 Agent tool adapter: expose **capabilities as tools** — `query` as the **only**
  knowledge-browsing tool (D3), plus `plan`, `spec_read`, `create_workspace`. No raw
  Read/Glob/Grep browse tool. (FR-2, FR-9, FR-10; [[12-assistant]])
- [x] T022 Write-guard on every agent tool that can write: route through
  `vault.guard_write_path`; never expose an unguarded write. (FR-11; P2; invariant "raw never rewritten")
- [x] T023 Consequential classification: route risky/destructive/external/mutating requests
  through the existing `plan` path; store `pending_plan`, reply that approval is required,
  and do **not** mutate in-turn. (FR-5, FR-6; P8; D2)
- [x] T024 Approval handler: when `approve=True` (or the turn approves the stored plan),
  execute the conversation's `pending-plan` via the capability layer, then clear it; set
  `executed: true`. All approvals come from the user — no auto-approval. (FR-5; D2)
- [x] T025 Workspace resolution: default when omitted; **create only on explicit user request**
  via `create_workspace` tool; report a missing/misspelled named workspace instead of creating it. (FR-10; P13; D1)

## Core — streaming & resume

- [x] T030 `capabilities.ask_stream(...)`: async generator yielding accumulated reply +
  `conversation_id`; final value marks completion (+ `pending_plan`/`executed`). (FR-4)
- [x] T031 Resume by `conversation_id` from the store, including **after a service restart**
  (context reconstructed from `sessions/`, not memory). (FR-3, FR-13)

## Interfaces (REST surface)

- [x] T040 `POST /api/chat` in `app/api.py` over `capabilities.ask()`. (FR-1, FR-9)
- [x] T041 `POST /api/chat/stream` as SSE (`text/event-stream`) over `ask_stream()`; final
  event carries `"done": true`. (FR-4; plan Data Contracts)
- [x] T042 [P] Ensure Swagger documents the new models/endpoints (auto via FastAPI); add
  summaries/tags consistent with existing routes. (FR-9)

## Validation (map to AC & invariants)

- [x] T050 AC-1: chat returns a coherent reply; knowledge question yields ≥1 citation when
  supporting pages exist. (FR-1, FR-2)
- [x] T051 AC-2: follow-up with returned `conversation_id` is context-aware. (FR-3)
- [x] T052 AC-3: consequential request returns a `pending_plan` and makes **no** mutation that turn. (FR-5)
- [x] T053 AC-4: routine question answers directly without a forced plan. (FR-6)
- [x] T054 AC-5: a `sessions/` conversation record exists after any turn. (FR-7)
- [x] T055 AC-6: streamed and full-reply modes converge to identical final content. (FR-4)
- [x] T056 AC-7: parity test enumerating capabilities across REST and chat. (FR-9; P9; [[20-testing]])
- [x] T057 AC-8: no turn writes under `vault/raw/` or edits an existing `log.md` line. (FR-11; P2/P6)
- [x] T058 AC-9: default workspace when omitted; missing named workspace reported; explicit request creates it. (FR-10)
- [x] T059 AC-10: a conversation resumed **after a restart** continues in context and a
  pre-restart pending plan can still be approved and executed. (FR-13; D2)

## Dependencies

- T002, T010 precede T020; T015 precedes T020 (conversation store), T031, T059.
- T016 precedes T023/T024 (pending-plan lifecycle).
- T020 precedes T021–T025, T030, T031, T040, T041.
- T023 precedes T024 (a plan must be stored before it can be approved).
- T030 precedes T041; T040 + T041 precede T056 (parity test).

## Resolved decisions (from spec.md)

- **D1** — chat may create a workspace only on explicit user request, via the `create_workspace`
  tool; never as a silent side effect. (T025)
- **D2** — all approvals are asked back to the user; a stored `pending-plan` is executed only
  on an explicit approval turn. (T016, T023, T024)
- **D3** — the agent browses via the `query` capability; capabilities are its tools; no raw
  filesystem browse tool. (T021)
