# Implementation Plan: Product Owner Chat

**Feature ID:** `002-assistant-chat` · **Spec:** [`spec.md`](spec.md)
**Status:** Draft
**Created:** 2026-08-16 · **Last Updated:** 2026-08-16

> Describes **how**. Turns [`spec.md`](spec.md) into architecture over the existing `app/`
> capability layer. Requirements are referenced (FR-n, AC-n), not restated. Undecided
> technical choices are in [`plan-tbd.md`](plan-tbd.md). Endpoint URLs below are
> illustrative, not binding — the binding constraint is capability parity (P9).

## Constitution Check

- [x] **P1 Vault is source of truth** — conversations persist to `sessions/`; answers come
  from workspace content; no separate chat datastore. ([[03-vault]], [[06-conversations]])
- [x] **P2 `vault/raw/` immutable** — the agent's write tools are routed through the existing
  `vault.guard_write_path`; `vault/raw/` is read-only. ([[18-security]])
- [x] **P3 Pipeline direction** — chat writes only to `sessions/`; promotion to `vault/wiki/`
  happens later via dreaming/ingest, not inside a chat turn. ([[06-conversations]])
- [x] **P4 Zettelkasten discipline** — chat does not hand-write concepts; any concept
  creation goes through existing ingestion helpers. ([[05-zettelkasten]])
- [x] **P5 Concept lifecycle** — unaffected; chat never mutates `usage-count` directly.
- [x] **P6 Traceability** — answers carry citations (via `query`); `log.md` stays
  append-only; each turn appends a session record. ([[17-observability]])
- [x] **P7 Reuse before create** — output/template production reuses the existing `produce`
  path; chat does not fork it. ([[21-outputs]])
- [x] **P8 Human-in-the-loop** — consequential requests return a plan via the existing
  `plan` capability; execution is a separate, approved turn. ([[09-planning]])
- [x] **P9 Interface parity** — chat is one more surface over the same `app/capabilities`
  module; a parity test enumerates capabilities across REST and chat. ([[12-assistant]], [[13-api]], [[14-chat]])
- [x] **P10 Portability** — no vector store; session files are Markdown + YAML. ([[19-non-functional]])
- [x] **P11 Continuous specification generation** — untouched here; chat can *request*
  spec drafts through existing capabilities. ([[07-specification-model]])
- [x] **P12 Risk-governed mutations** — consequential classification reuses the capability
  layer's risk/plan path; no silent mutation from chat. ([[10-risk-engine]])
- [x] **P13 Multi-workspace** — the conversation resolves a workspace via the existing resolver;
  default when omitted. ([[03-vault]])

## Technical Context

- **Language / runtime:** Python 3.13+ (matches `app/`).
- **Agent runtime:** `claude-agent-sdk` (already a dependency) — `include_partial_messages`
  for streaming; the agent's **tools are the capability functions** (`query`, `plan`,
  `create_workspace`, `spec_read`, …), not raw filesystem access (D3). This mirrors the proven
  streaming pattern archived in `__OLD__/core.py` (query → SystemMessage init → StreamEvent
  deltas → ResultMessage), but re-pointed at the capability layer so every answer is cited
  and every mutation is governed.
- **Conversation store (durable):** the workspace's `sessions/` is the **source of truth** for a
  conversation (P1). We key each conversation by our own `conversation_id` and reconstruct
  context from its session file, so a conversation resumes **after a restart** (D2/FR-13).
  Any SDK-native session id is treated as a disposable cache, persisted alongside but never
  authoritative.
- **REST:** FastAPI (existing `app/api.py`); SSE for streaming (`StreamingResponse`,
  `text/event-stream`).
- **Persona / system prompt:** assembled from `memory/constitution.md` + selected numbered
  specs (Product Owner identity), realizing feature 001 task T003.
- **Storage:** filesystem only — conversation trace as Markdown under `sessions/`.
- **Dependencies on other features:** builds directly on feature 001's `app/capabilities`
  (`query`, `plan`, `ingest`, `spec_read`, `list/create/get workspace`) and `app/vault`
  (resolver, guard, `append_log`). Realizes 001 tasks **T071–T074**.

> Rationale: the capability layer already exists and is the parity boundary (P9). This
> feature adds (a) an `ask()` capability that orchestrates the agent, and (b) chat REST
> endpoints — nothing bypasses `app/capabilities`.

## Architecture Overview

```text
POST /api/chat (+ /stream)  ─┐
(future GUI)                 ┘── app/capabilities.ask() ──► agent runtime (claude-agent-sdk)
                                        │                        │ tools = capabilities
                                        │                        ▼
                                        │             query · plan · spec_read · create_workspace
                                        ▼                        │  (all governed)
                          conversation store (sessions/)  ◄──────┘
                          load-on-resume · append-each-turn   app/vault (resolver+guard+log)
```

- The chat endpoint is thin: validate request → call `capabilities.ask()` → stream/return.
- `ask()` owns: resolve the conversation (load prior turns from `sessions/` by
  `conversation_id`), resolve the workspace, load the persona prompt, run the agent with
  **capabilities as its tools**, classify consequential vs. routine, and append the turn to
  the conversation's session file.
- The agent browses knowledge **only via `query`** (cited); it never reads workspace files
  directly (D3). Any capability that writes goes through `vault.guard_write_path`.
- Consequential requests stop at a **plan**; the plan is persisted with the conversation and
  executed only after the user's explicit approval arrives in a later turn (D2).

## Components

- **`capabilities.ask(workspace, message, conversation_id) -> ChatAnswer`** — surface-agnostic
  orchestration entry point (the parity boundary for chat). Loads/creates the conversation,
  runs the agent, appends the turn, returns final reply + `conversation_id` + citations
  (+ `plan` when consequential). (FR-1..FR-6, FR-8, FR-12, FR-13)
  - reads: conversation from `sessions/`; workspace via resolver; persona from `memory/` + `specs/`.
  - writes: the turn (and any pending plan) into the conversation's session file.
- **Persona/prompt assembler** — builds the Product Owner system prompt from the
  constitution + a curated set of numbered specs (00, 01, 07, 09, 13, 14). (FR-8; 001 T003)
- **Agent tool adapter** — exposes **capabilities as the agent's tools**: `query` (the only
  knowledge-browsing tool, D3), `plan`, `spec_read`, `create_workspace`, and (gated) `ingest`.
  No raw `Read/Glob/Grep` browse tool. Every writing capability enforces
  `vault.guard_write_path`. (FR-2, FR-5, FR-9, FR-10, FR-11)
- **Conversation store** — durable record under `<workspace>/sessions/`, keyed by
  `conversation_id`. Provides `load(conversation_id)` (reconstruct context, incl. any pending
  plan) and `append_turn(...)`; append-only, never edits prior lines. Resumable across
  restarts (D2/FR-13). (FR-3, FR-7, FR-13; [[06-conversations]])
- **Approval handler** — when a turn is an approval of a pending plan (looked up from the
  conversation), execute the plan via the capability layer; otherwise a consequential
  request stops at the plan and stores it pending. (FR-5, D2)
- **Chat REST surface** — `POST /api/chat` (full reply) and `POST /api/chat/stream` (SSE),
  in `app/api.py`, both over `capabilities.ask()`. (FR-1, FR-4, FR-9)

## Data & File Contracts

- **Chat request** (both endpoints):
  ```json
  { "message": "string", "workspace": "optional-selector", "conversation_id": "optional-id",
    "approve": false }
  ```
  `conversation_id` omitted → start a new conversation (id returned). `approve: true`
  signals the user is approving the conversation's pending plan (D2/FR-5).
- **Chat response** (`/api/chat`):
  ```json
  { "workspace": "name", "conversation_id": "id", "reply": "string",
    "citations": [{"page": "vault/wiki/...md", "excerpt": "..."}],
    "pending_plan": null, "executed": false }
  ```
  When the request is consequential, `pending_plan` is populated (same shape as
  `models.Plan`), `reply` explains approval is required, and nothing is mutated. When a
  turn approves a stored plan, it is executed and `executed: true`. (FR-5, D2)
- **Streaming response** (`/api/chat/stream`): `text/event-stream`; each event is
  `data: {json}` carrying the accumulated `reply` + `conversation_id`; the final event adds
  `"done": true` (and `pending_plan`/`executed` where relevant). (FR-4)
- **Session file (durable conversation record)**: `<workspace>/sessions/<conversation_id>.md`
  — one file per conversation so it is loadable/resumable by id (D2/FR-13).
  ```yaml
  ---
  Category: session
  conversation-id: <id>
  Created: YYYY-MM-DD
  sdk-session-id: <disposable cache, optional>
  pending-plan:            # present only while a plan awaits approval (FR-13)
    request: "<original request>"
    plan: { ...models.Plan... }
  ---
  ## [YYYY-MM-DD HH:MM] user
  <message>
  ## [YYYY-MM-DD HH:MM] assistant
  <reply>
  ```
  Turns are append-only. The `pending-plan` frontmatter block is the one mutable field
  (set when a plan is proposed, cleared on approval/execution); turn history is never
  edited. Aligns with `sessions/` role in [[03-vault]] §4 and [[06-conversations]].

## Interfaces / Contracts

Capability-layer additions (the only path from a surface to the agent, P9):

- `ask(workspace, message, conversation_id, approve=False) -> ChatAnswer` — non-streaming.
- `ask_stream(workspace, message, conversation_id, approve=False) -> AsyncIterator[ChatDelta]` — streaming.

REST (paths illustrative; parity is the constraint):

- `POST /api/chat` → `ChatAnswer`
- `POST /api/chat/stream` → SSE of `ChatDelta`

Pydantic models added to `app/models.py`: `ChatRequest`, `ChatAnswer`, `ChatDelta`
(reusing `Citation` and `Plan`). Swagger documents them automatically.

## Alternatives Considered

- **Deterministic orchestration (no LLM agent), pure capability calls** — simpler and
  fully testable, but cannot hold open-ended conversation or synthesize across pages;
  rejected as the primary path. May back a "fast" non-agent mode later → `plan-tbd.md`.
- **Give the agent raw filesystem tools (Read/Glob/Grep) to browse** — the archived
  `__OLD__` approach. **Rejected** (D3): browsing goes through `query` so every answer is
  cited and the parity boundary (P9) holds. The agent gets capabilities as tools, not the
  filesystem.
- **Auto-approval flag for consequential work** — **rejected** (D2): all approvals are
  asked back to the user; execution only happens on an explicit approval turn.
- **In-memory-only conversations / DB-backed sessions** — rejected; conversations must be
  durable Markdown under `sessions/` and resumable after restart (P1/P10, FR-13).
- **Reviving the Gradio UI** — out of scope (Non-Goal); this feature is API-only.

## Risks & Mitigations

- **Correlating an approval to its pending plan** → store the pending plan in the
  conversation's session frontmatter; an `approve` turn executes that stored plan, then
  clears it. Correlation key = `conversation_id`. (Implementation detail; mirrors 001 TBD-2.)
- **Agent bypassing the guard via a write tool** → only expose writes through capability
  functions that call `vault.guard_write_path`; never hand the agent an unguarded `Write`,
  and give it no raw filesystem browse tool (D3).
- **Parity drift** (a chat-only ability) → CI parity test enumerating capabilities across
  REST and chat (AC-7; [[20-testing]]).
- **Resume correctness after restart** → reconstruct context from the session file, not
  memory; test explicitly (AC-10).
- **Session/context growth on long threads** → one file per conversation; cap replayed
  history and rely on the SDK session cache when valid; dreaming compacts later.
- **Cost/latency of streaming agent** → offer non-streaming `ask()` for programmatic
  callers; stream only on `/stream`.

## Rollout / Sequencing

- **MVP:** `ask()` (non-streaming) with the Product Owner persona and `query` as the
  browsing tool; `POST /api/chat`; durable conversation store (create + resume by
  `conversation_id`); default-workspace resolution. Consequential requests return a
  `pending_plan` (no execution).
- **Then:** approve-and-execute (`approve: true` → run the stored plan); `/api/chat/stream`
  (SSE); parity test (AC-7); resume-after-restart test (AC-10).
- **Later:** add `create_workspace` and gated `ingest`/`produce` as agent tools; optional
  non-agent fast mode; richer citations.
