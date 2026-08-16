# Feature Specification: Product Owner Chat

**Feature ID:** `002-assistant-chat`
**Status:** Draft
**Created:** 2026-08-16 · **Last Updated:** 2026-08-16

> Describes **what** and **why**. Realizes the chat surface deferred by feature
> [`001-leader-assistant`](../001-leader-assistant/tasks.md) tasks T071–T074, over the
> capability layer already built in `app/`. Primary spec references: [[14-chat]],
> [[12-assistant]], [[13-api]], [[09-planning]], [[06-conversations]], [[00-product-vision]].

## Summary

A conversational interface to the assistant **acting as the project's AI Product
Owner**. A user (developer, stakeholder) can chat with it to ask about the project,
retrieve cited knowledge from the vault, request and review plans for consequential
work, and co-author specifications — all through natural language. The chat is a
*presentation* of the same capability layer the REST API exposes (Constitution P9); it
adds no capability the API lacks. Every exchange is captured to `sessions/` so it can
later feed knowledge maturation via dreaming.

## Goals

- Let a human hold a multi-turn conversation with the assistant about this project.
- Have the assistant answer from the vault with **citations**, never from thin air.
- Present the assistant with a consistent **Product Owner** identity and behavior derived
  from the constitution and the numbered specs.
- Route consequential requests through **plan-first** review before any mutation (P8).
- **Persist every conversation** turn to `sessions/` automatically (P-conversations).
- Support **resumable** conversations (continue a prior thread) and **incremental**
  (streamed) responses so long answers appear as they are produced.
- Keep strict **parity** with the API: each chat ability is a capability also reachable
  over REST (P9).

## Non-Goals

- A graphical/web chat UI (the archived Gradio UI in `__OLD__/` is not resurrected here;
  this feature delivers the chat **API** surface only).
- New knowledge/governance engines — dreaming, risk-branching, continuous spec
  generation are separate features; this feature *invokes* existing capabilities and
  surfaces plans, it does not implement those engines.
- External PM actions (Jira/Linear/etc.) — out of scope; see [[15-integrations]].
- Authentication / multi-user accounts — the service remains local and single-operator.

## User Scenarios

- **Scenario 1 — Ask about the project:** As a developer, when I ask "what does the risk
  engine decide?", the assistant searches the selected vault and answers with citations
  to the pages it used, so that I can trust and verify the answer.
- **Scenario 2 — Continue a thread:** As a user, when I send a follow-up referencing my
  previous question, the assistant remembers the conversation (via a returned
  conversation id) and answers in context, so that I don't repeat myself.
- **Scenario 3 — Plan-first for consequential work:** As a stakeholder, when I say
  "rewrite the onboarding spec", the assistant returns a **plan** for my review rather
  than silently editing, so that I stay in control of consequential changes (P8).
- **Scenario 4 — Streamed answer:** As a user, when I ask a broad question, I see the
  answer stream in progressively rather than waiting for the whole reply, so that long
  responses feel responsive.
- **Scenario 5 — Captured for learning:** As the project owner, after a chat where I
  correct the assistant, that correction is recorded in `sessions/`, so that a later
  dreaming pass can promote it into durable knowledge (P-conversations AC4).
- **Scenario 6 — Choose a vault:** As a user working across projects, when I name a vault
  in my request, the conversation operates on that vault; otherwise it uses the default
  (P13).

## Functional Requirements

Numbered, testable, unambiguous.

- **FR-1:** The system MUST accept a chat message plus an optional conversation id and an
  optional vault selector, and return the assistant's reply.
- **FR-2:** The assistant MUST answer knowledge questions by retrieving vault content
  through the **`query` capability** (not by reading files directly), and MUST include the
  citations `query` returns whenever it makes a factual claim about the project. *(Resolves
  Q3: the agent browses data by calling `query`.)*
- **FR-3:** The system MUST support resuming a prior conversation: given a conversation id
  returned by an earlier turn, the next turn continues in that context.
- **FR-4:** The system MUST support incremental (streamed) delivery of the reply, in
  addition to a single full-reply response.
- **FR-5:** For **consequential** requests (those the risk model would flag, destructive
  changes, external actions, or any vault mutation), the assistant MUST present a plan for
  review and MUST NOT execute the change within the same turn. Execution MUST wait for the
  user's **explicit approval** in a subsequent turn; there is **no auto-approval** path.
  *(Resolves Q2: all approvals are asked back to the user.)* (P8, [[09-planning]])
- **FR-6:** For **routine** requests (question answering, retrieval, drafting a
  suggestion), the assistant MAY respond directly without a plan (P8 autonomy boundary).
- **FR-7:** Every chat turn (user message and assistant reply) MUST be persisted to the
  selected vault's `sessions/` automatically ([[06-conversations]] AC1).
- **FR-8:** The assistant MUST present a consistent **Product Owner** persona: its
  behavior is governed by the constitution and the numbered specs, and it speaks about the
  project as its owner (prioritizing specifications, knowledge compounding, and
  human-in-the-loop governance).
- **FR-9:** Every ability offered in chat MUST be invocable through the REST API and vice
  versa (P9). Chat MUST NOT reach the vault except through the shared capability layer. The
  assistant operates by **calling capabilities as tools** (`query`, `plan`, `create_vault`,
  `spec_read`, …) — the same capabilities the REST API exposes. *(Resolves Q1/Q3: chat
  calls the API as tools.)*
- **FR-10:** If no vault selector is supplied, the conversation MUST operate on the
  configured default vault (P13). The assistant MAY create a vault **only when the user
  explicitly requests it**, by calling the vault-creation capability as a tool (which, being
  a mutation, follows the approval flow in FR-5). It MUST NOT silently create a vault when
  resolving an omitted or misspelled selector; such a missing named vault MUST be reported
  clearly. *(Resolves Q1.)*
- **FR-11:** The assistant MUST NOT write to `raw/` and MUST NOT edit existing `log.md`
  entries as a side effect of any chat turn (P2, P6).
- **FR-12:** When the assistant makes assumptions to avoid unnecessary clarifying
  questions, it MUST state those assumptions in its reply ([[09-planning]] AC3).
- **FR-13:** Every chat MUST belong to a **durable conversation** identified by a
  conversation id: the full turn history is stored under `sessions/` and a conversation MUST
  be **resumable by id even after a service restart** (the `sessions/` record, not in-memory
  state, is the source of truth per P1). A pending plan awaiting approval (FR-5) MUST be
  recoverable from the conversation so the user can approve it in a later turn.

## Key Entities & Concepts

- **Conversation** — a durable, resumable thread of turns identified by a conversation id.
  Its authoritative record lives in `sessions/` (survives restarts); any in-memory state is
  a cache of that record (P1).
- **Turn** — one user message and the assistant's reply.
- **Product Owner persona** — the assistant's identity and operating rules, sourced from
  the constitution + numbered specs.
- **Citation** — a reference from an answer to the vault page(s) that support it.
- **Plan** — the reviewable proposal returned for consequential requests (already modeled
  by the capability layer).
- **Session record** — the `sessions/` file capturing the conversation for later dreaming.
- **Vault selector** — names which vault the conversation operates on (default when
  omitted).

## Constraints & Assumptions

- **Constitution:** P1 (vault is truth), P2 (`raw/` immutable), P6 (traceability /
  append-only log), P8 (human-in-the-loop), P9 (interface parity), P10 (portability),
  P13 (multi-vault) all apply.
- Builds on the existing `app/` capability layer (`query`, `plan`, `ingest`, `spec_read`,
  vault resolution) — this feature adds a conversational orchestration capability, not a
  parallel data path.
- **Assumption:** conversations are single-operator and local; no auth is required. If
  this becomes multi-user, session isolation and identity must be revisited.
- **Assumption:** the assistant reaches the model via an agent runtime that can call the
  capability layer as tools; the exact runtime is a plan concern, not a spec concern.

## Acceptance Criteria

- [ ] **AC-1:** A chat request with a message returns a coherent reply; a knowledge
  question yields an answer with at least one citation when supporting pages exist. (FR-1, FR-2)
- [ ] **AC-2:** Sending a follow-up with the returned conversation id produces a
  context-aware reply. (FR-3)
- [ ] **AC-3:** A consequential request returns a plan and makes **no** vault mutation in
  that turn; the mutation happens only after explicit approval. (FR-5, P8)
- [ ] **AC-4:** A routine question answers directly without forcing a plan step. (FR-6)
- [ ] **AC-5:** After any chat turn, a corresponding record exists under the vault's
  `sessions/`. (FR-7, [[06-conversations]] AC1)
- [ ] **AC-6:** Streaming and full-reply modes both return the same final content. (FR-4)
- [ ] **AC-7:** For every chat ability there is an equivalent API capability, verified by
  a parity check. (FR-9, P9; mirrors [[20-testing]] parity invariant)
- [ ] **AC-8:** No chat turn writes under `raw/` or edits an existing `log.md` line. (FR-11, P2/P6)
- [ ] **AC-9:** With no vault selector, the default vault is used; a named missing vault is
  reported, not silently created; an explicit "create vault X" request creates it via the
  capability. (FR-10, P13)
- [ ] **AC-10:** A conversation resumed by id **after a service restart** continues in
  context, and a plan left pending before the restart can still be approved. (FR-13, P1)

## Resolved Decisions

- **D1 (was Q1) — Vault creation:** chat MAY create a vault, but only on explicit user
  request, by calling the vault-creation capability as a tool; never as a silent side
  effect of selector resolution. (FR-10)
- **D2 (was Q2) — Approval:** all consequential actions require the user's explicit approval
  in a follow-up turn; there is no auto-approval flag. The pending plan is stored with the
  conversation so approval can arrive in a later turn (even after restart). (FR-5, FR-13)
- **D3 (was Q3) — Tools:** the agent browses knowledge by calling the `query` capability
  (which returns citations); it does not read vault files directly. Capabilities are the
  agent's tools. (FR-2, FR-9)

## Open Questions

- None blocking. Implementation detail deferred to [`plan.md`](plan.md): the exact
  correlation key between an approval message and its pending plan (mirrors feature 001
  TBD-2), and the on-disk shape of a pending plan within the session record.

## Review Checklist

- [ ] No implementation details (how) leaked into this spec.
- [ ] Every requirement is testable.
- [ ] Scenarios cover the golden path and key edge cases.
- [ ] Complies with `memory/constitution.md`.
- [ ] Any local↔remote conflict captured in a `*-contradiction.md`, not silently resolved.
