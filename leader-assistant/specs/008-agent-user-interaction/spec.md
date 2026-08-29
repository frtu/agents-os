# Feature Specification: Agent–User Interaction (Approval, Clarification & Live Feedback)

**Feature ID:** `008-agent-user-interaction`
**Status:** Implemented (see [`plan.md`](plan.md))
**Created:** 2026-08-23 · **Last Updated:** 2026-08-23

> Describes **what** and **why**, never **how**. Realizes the clarification & human-in-the-loop
> interaction model of [[09-planning]] (§2–§3) and the human-control principle (P8) as a concrete,
> **asynchronous** exchange between the backend agent and the frontend, on top of the chat surface
> ([[002-assistant-chat]] FR-13/FR-14), the web UI ([[003-assistant-ui]], [[004-assistant-sidebar]]),
> and interface parity (P9, [[13-api]], [[14-chat]]). Transport, storage shape, and UI framework
> details are deferred to `plan.md`.

## Summary

While working on a task the assistant often needs a decision from the human — permission to do
something consequential, or a choice between genuinely different approaches. Today the only channel
is a plain chat reply plus a follow-up message; the user has to know to re-send an approval, nothing
signals that the agent is *blocked waiting*, and there is no structured way to offer a small set of
alternatives. This feature adds a first-class **agent→user interaction channel**: mid-task the
backend can **pause and ask**, streaming a structured **Interaction Request** to the frontend, which
renders it as a distinct, visually-obvious **interaction card** and streams the user's answer back so
the task resumes. There are three kinds of request — **notification** (live progress, no decision),
**approval** (a single yes/no consent, the simplest clarification), and **clarification** (a choice
among 2–4 distinct proposals). Every card always offers a **"chat about it"** escape hatch to discuss
the decision in focused context. The exchange is asynchronous and durable, so a user who reloads or
steps away can still find and answer a pending question, and every interaction is captured to the
conversation for traceability. It keeps strict parity: the same request/response protocol is available
over REST for machine callers (P9).

## Goals

- Let the backend, mid-task, **ask the user and wait** — pausing consequential progress until it has
  an answer or a timeout — without the user needing to know a magic follow-up incantation.
- Provide **three interaction kinds**: **notification** (informational/progress), **approval** (binary
  consent on one obvious proposal), and **clarification** (pick one of 2–4 distinct proposals).
- Treat **approval as the degenerate case of clarification** (one proposal → yes/no consent), so both
  share one protocol, one card, and one response channel.
- Always give the user a **"chat about it"** option on approval and clarification, so a decision can
  be discussed in focused context before it is made.
- Deliver **rich, live visual feedback**: an interaction card with an **animated progress indicator**
  and a **configurable countdown** (default **30 seconds**) that makes it obvious the agent is waiting.
- Keep the exchange **asynchronous and durable**: the backend streams the request; a pending
  interaction survives disconnect/reload/restart so it can still be answered (builds on
  [[002-assistant-chat]] FR-13/FR-14).
- Preserve **human-in-the-loop** (P8): no consequential/external/destructive action runs without an
  explicit approval or an explicit authorizing selection; a timeout or decline never authorizes.
- Keep **parity** (P9): the interaction request/response protocol is reachable over both the chat/UI
  surface and the REST API; neither has a capability the other lacks.
- **Capture** every interaction (request, options, response or timeout, and any discussion) into the
  conversation's `sessions/` record for traceability and later dreaming ([[06-conversations]], P6).

## Non-Goals

- **No new decision *engine*.** This feature is the *interaction channel*; *when* to ask and *what*
  to propose is governed by [[09-planning]] (§3 materiality) and [[10-risk-engine]]. This spec does
  not change those rules.
- **No multi-select / free-form option sets.** Clarification options are **single-select** (radio),
  bounded to **2–4** proposals plus the constant "chat about it" affordance; approval is a single
  proposal (yes/no). Ranking, multi-pick, and >4 options are out of scope.
- **No transport, storage-format, or UI-framework decisions here** — SSE vs WebSocket, the on-disk
  shape of a pending interaction, the exact card markup/animation — all belong in `plan.md`.
- **No authentication / multi-user.** The service stays local and single-operator; "the user" is one
  human. Concurrent human responders are out of scope.
- **No general async job/queue system.** This is scoped to a single in-flight conversational task
  asking its own user; it is not a background-job framework.

## User Scenarios

- **Scenario 1 — Security consent (approval):** As a user, when the agent needs to do something
  sensitive (e.g. run a shell command a skill requests), it shows a distinct **approval card**:
  one proposal, **Yes / No**, a **"chat about it"** option, and a turning progress wheel counting down
  from 30s. I click **Yes** and it proceeds; if I click **No** (or it times out) it does **not**
  proceed and tells me so.
- **Scenario 2 — Choose an approach (clarification):** As a user, when my request is ambiguous, the
  agent presents **2–4 distinct proposals** as selectable **radio cards** plus a final **"chat about
  it"** option. I pick one and the agent continues with exactly that choice.
- **Scenario 3 — Discuss before deciding ("chat about it"):** As a user, when I'm unsure, I click the
  card's **"chat about it"** option; the conversation goes **deep into that specific decision**
  (scoped to the pending interaction's context — its proposals and rationale). After we discuss, I can
  still pick an option or approve, and the task resumes; the agent may re-present an **updated** card.
- **Scenario 4 — Start something else while a question is pending:** As a user with a clarification
  card open, when I type in the **bottom chat box**, it starts a **new task** — it does **not** answer
  the pending card. The pending interaction stays visible and answerable. The card's "chat about it"
  is the *only* way to talk *about* the pending decision.
- **Scenario 5 — I walked away (timeout):** As a user who left the screen, when the countdown reaches
  zero, the pending approval/clarification resolves to its **safe default** (no consequential action
  taken); the card is dismissed and the agent reports **"Something goes wrong, please retry later"** so
  I'm never surprised by an action I didn't authorize and know to re-ask.
- **Scenario 6 — I reloaded (durability):** As a user who refreshed the page or reconnected while a
  question was pending, when the UI reloads, the **pending interaction card reappears** with its
  options and I can still answer it — the agent didn't lose the question.
- **Scenario 7 — "I'm working on it" (notification):** As a user, during a longer operation the agent
  streams a **notification card** (a message plus an animated progress wheel) so I can see it is busy;
  it needs no decision and **auto-dismisses** after its timeout.
- **Scenario 8 — Machine caller (parity):** As an API client, when I start a task and the agent needs
  input, I receive a **structured interaction request** in the response stream (kind, prompt, options,
  interaction id, timeout); I **POST a structured response** referencing that id, and the task
  resumes — the same protocol the UI uses (P9).
- **Scenario 9 — Agent asks on its own (agent-initiated clarification):** As a user, when I send an
  ambiguous request (e.g. "run multi-agent mode") the agent, on its own judgment, presents a
  **clarification card** with 2–4 distinct proposals instead of a prose bullet list, and continues with
  the option I pick. When my request is clear it just answers — no card. (FR-18)

## Functional Requirements

Numbered, testable, unambiguous.

### Interaction channel

- **FR-1 (ask-and-wait):** While processing a task, the backend MUST be able to emit one or more
  **Interaction Requests** to the frontend and, for a *blocking* request (approval, clarification),
  **pause** the gated work until it receives a matching **Interaction Response** or the request times
  out. The exchange MUST be **asynchronous** — the backend streams the request to the frontend rather
  than returning it only at the end of the turn.
- **FR-2 (three kinds):** An Interaction Request MUST be exactly one of three kinds:
  **notification**, **approval**, or **clarification**. Every request MUST carry a unique
  **interaction id** (scoped to its conversation), a human-readable **prompt/message**, and a
  **timeout** (FR-9).
- **FR-3 (notification):** A **notification** request is informational and requires **no decision**.
  It MUST render as a live status card with an **animated progress indicator** and MUST **auto-expire**
  after its timeout (default 30s, FR-9). It MAY offer a single non-decision control (e.g. dismiss /
  cancel). Notifications MUST NOT block gated work and MAY be streamed repeatedly during a task.
- **FR-4 (approval = simple clarification):** An **approval** request presents **exactly one proposal**
  and asks for **binary consent (Yes / No)**. It is the simplest clarification and MUST use the same
  card and response channel as clarification. It is the required gate for consequential/security-
  sensitive actions (P8, [[10-risk-engine]]). A **No** or a **timeout** MUST NOT execute the proposed
  action (FR-14). An approval card MUST always include the **"chat about it"** option (FR-7).
- **FR-5 (clarification):** A **clarification** request presents **between 2 and 4** distinct
  proposals as **mutually exclusive, single-select (radio)** options, plus a final constant **"chat
  about it"** option. The user selects **exactly one** proposal to proceed. The proposals SHOULD be the
  agent's *top, genuinely different* options (not trivial variants).
- **FR-6 (option bounds):** The interaction card MUST support **1–4** proposal options plus the
  constant "chat about it" affordance: an **approval** is the **1-proposal** case (rendered as Yes/No
  consent); a **clarification** is the **2–4-proposal** case. Requests outside these bounds MUST be
  rejected as malformed (never rendered).
- **FR-7 ("chat about it" always available):** Approval and clarification cards MUST **always** offer a
  final **"chat about it"** option. Selecting it MUST open a **focused discussion scoped to the pending
  interaction's context** (its prompt, proposals, and rationale) **without resolving** the interaction.
  After discussing, the user MUST still be able to select a proposal / approve, and the agent MAY
  **re-present an updated interaction** for the same decision — a re-presented interaction is a **new
  interaction with a new id** that **supersedes** the prior one (the prior id becomes non-answerable,
  D9). While in "chat about it", the pending interaction's countdown is **paused** (FR-9, D8).
- **FR-8 (new-task vs. deep-context boundary):** The always-present **bottom chat box** MUST start a
  **new top-level task/turn** and MUST **not** be interpreted as an answer to any pending interaction.
  The **only** way to enter the pending interaction's deep context is the card's **"chat about it"**
  option (FR-7). The UI MUST make this distinction visually clear.

### Feedback, timing & presentation

- **FR-9 (timeout, configurable, default 30s):** Every Interaction Request MUST carry a **timeout**.
  The system default MUST be **30 seconds**, MUST be **configurable** (system-wide default with an
  optional per-request override), and the **remaining time SHOULD be visible** (an animated wheel /
  countdown). On expiry: a **notification** auto-dismisses; a **blocking** request (approval,
  clarification) resolves to its **safe default = no proposal selected / not approved**, so gated work
  does **not** proceed (FR-14). Timeout of a blocking request MUST **abort** the interaction and report
  the exact message **"Something goes wrong, please retry later"** to the user (D6). The countdown MUST
  **pause** while the user is in the card's "chat about it" discussion and **reset** to a fresh timeout
  when the interaction is (re-)presented afterward (D8). The auto-expire MUST fire **at most once per
  interaction** and MUST derive its remaining time only from the **currently-live** card, never from an
  already-resolved or superseded one, so it cannot re-trigger itself (D11).
- **FR-10 (distinct interaction card):** Approval and clarification MUST render as a **visually
  distinct card** — clearly differentiated from ordinary chat messages — so the user immediately
  recognizes that **their input is required**. The card MUST render **as an assistant message within the
  conversation scroll** (part of the message history, a left-aligned assistant bubble — not an element
  exterior to the message list); the human's selection then appears as a user message. It stays clearly
  differentiated via its accent border and inline option controls. The card MUST show the prompt, the
  selectable options as **selectable choices**, the "chat about it" option, and the progress/countdown
  indicator. Options SHOULD be presented as selectable cards that read as actionable.

### Async, durability, parity & capture

- **FR-11 (async & durable):** A **pending interaction** MUST be **recoverable** after a client
  disconnect, page reload, or service restart, so the user can still answer it (the durable record,
  not in-memory state, is the source of truth — P1; builds on [[002-assistant-chat]] FR-13). On
  reconnect the frontend MUST be able to re-render any still-pending interaction for the active
  conversation.
- **FR-12 (parity, P9):** The interaction request/response protocol MUST be available on **both** the
  chat/UI surface and the **REST API**. A machine caller MUST be able to receive a structured
  Interaction Request (kind, prompt, options, interaction id, timeout) and submit a structured
  Interaction Response referencing that id, with equivalent effect to a UI click. No part of this
  protocol may exist on only one surface ([[13-api]], [[14-chat]]).
- **FR-13 (capture, P6):** Every interaction MUST be recorded into the conversation's `sessions/`
  record: the request (kind, prompt, the options offered), the resolution (which option was chosen, or
  approved/declined, or timed out), and any **"chat about it"** discussion turns. This makes decisions
  auditable and available to later dreaming ([[06-conversations]]).
- **FR-14 (human-in-the-loop gate, P8):** No consequential, external, or destructive action MAY execute
  without an **explicit approval** or an **explicit clarification selection that authorizes it**. A
  **decline**, a **timeout**, "chat about it", or a **new task** (FR-8) MUST NEVER be treated as
  authorization. This feature is the delivery vehicle for P8; it does not widen the autonomy boundary
  of [[09-planning]] §4.
- **FR-15 (one blocking interaction at a time):** A single task MUST have **at most one** *blocking*
  interaction (approval/clarification) outstanding at once, and MUST NOT proceed with the gated work
  while it is outstanding. Non-blocking **notifications** MAY stream concurrently.
- **FR-16 (id-scoped, idempotent responses):** An Interaction Response MUST reference the interaction
  **id** it answers. Responding to an **unknown**, **already-resolved**, or **expired** interaction
  MUST be **rejected without side effects** — in particular it MUST NOT cause a proposed action to run
  twice or run after a timeout.
- **FR-17 (relationship to plan-first approval):** The existing plan-first approval flow
  ([[002-assistant-chat]] FR-5: a consequential request returns a `pending_plan` approved by a
  follow-up turn) MUST be expressible as an **approval** interaction under this protocol, so the user
  experiences one consistent approval mechanism. Backward compatibility of the existing chat
  approve-to-execute path is an implementation concern for `plan.md`; this spec requires only that the
  *behavior* (plan shown, explicit approval before execution, P8) is preserved.
  - **Refined by [[009-approval-optimization]]:** *when* an approval card appears is decided there —
    only when an **executable** capability of effect tier `approval` is about to run and the operator
    has not granted standing consent (`auto_approve`). Approval **outcomes** are therefore decided
    **exclusively by the capability layer** and a card is never raised for a request the build cannot
    execute (009 FR-3/FR-4/FR-12). Notification and clarification cards are unchanged, stay
    agent-raised (FR-18), and remain on a distinct code path so the UI can tell the two apart.
  - **Extended by [[010-agent-approval-channel]]:** an approval **request** may also originate from the
    agent's own judgment (010 FR-1), and with trust mode on the layer resolves it as approved
    on the operator's behalf in the same turn, surfaced as inert already-decided context (010
    FR-4/FR-5).
- **FR-18 (agent-initiated interactions):** During a routine chat turn the **agent itself** (the model,
  via its tool surface) MUST be able to raise an interaction, not only the deterministic plan-first path.
  The agent MAY raise a **clarification** (2–4 proposals, blocking) when a request is genuinely ambiguous
  or requires the user to choose among distinct approaches, and a **notification** (non-blocking) for
  brief status; a clarification raised this way MUST **pause** the turn and be surfaced to the frontend
  exactly like any other blocking interaction (FR-1), obeying the one-blocking-at-a-time rule (FR-15) and
  durability (FR-11). When a request is clear and actionable the agent MUST answer
  directly and MUST NOT raise a spurious card ([[09-planning]] §3: do not ask unnecessary questions).
  - **Amended by [[010-agent-approval-channel]] (ask ≠ grant):** the agent MAY **request** an approval
    through the governed channel (010 FR-1) — the request becomes a protocol Interaction of kind
    `approval` with an id, a durable record, a countdown and a resolution event. The agent MUST NOT
    **grant** one: the outcome is decided by the capability layer alone, from the human's answer or the
    operator's trust mode (010 FR-2), and the agent has no tool to answer its own request or to read,
    set, or bypass trust mode. The original rationale is preserved — the agent cannot manufacture its
    own *consent* — and strengthened, because forbidding the *structured* request only pushed the model
    into an ungoverned **prose** approval that trust mode cannot skip, the UI cannot re-present, and the
    audit trail cannot record.

## Key Entities & Concepts

- **Interaction Request** — a structured message from the backend asking the user to notice or decide
  something mid-task. Has an **id** (conversation-scoped), a **kind** (notification | approval |
  clarification), a **prompt**, zero–four **proposals**, a **timeout**, and (for blocking kinds) the
  constant **"chat about it"** affordance.
- **Interaction kind** — **notification** (no decision, auto-expiring progress), **approval** (one
  proposal, yes/no consent), **clarification** (2–4 proposals, single-select).
- **Proposal / Option** — one selectable choice the agent offers. For clarification these are the top
  distinct approaches; for approval the single thing being consented to.
- **"Chat about it" context** — a focused sub-discussion **scoped to a specific pending interaction**,
  entered only from the card, distinct from the global bottom chat box which starts new tasks.
- **Interaction Response** — the user's (or machine caller's) answer: a selected proposal, an
  approve/decline, or "chat about it" — always referencing the interaction id.
- **Timeout / safe default** — the countdown after which a request auto-resolves; for blocking kinds
  the safe default is **no authorization** (nothing consequential happens).
- **Pending interaction** — a blocking interaction awaiting a response; **durable** so it survives
  reload/restart and can be re-rendered and answered.
- **Interaction card** — the visually distinct UI surface that renders a request (progress indicator,
  countdown, radio options, "chat about it").

## Constraints & Assumptions

- **Constitution:** **P8** (human-in-the-loop for consequential work) is the core driver; **P9**
  (interface parity API == chat); **P1** (durable record, not memory, is truth); **P6** (traceability —
  capture interactions); **P13** (interactions operate within the active workspace's conversation).
- Builds directly on **[[002-assistant-chat]]**: the durable, resumable conversation store (FR-13) and
  the server-side running-status probe (FR-14) — a pending interaction is a natural extension of the
  same durable, recoverable state, and "running" may distinguish *computing* from *waiting on the user*.
- Builds on the **web UI** ([[003-assistant-ui]], [[004-assistant-sidebar]]): the interaction card and
  bottom chat box live in the existing chat surface; presentation is a pure surface over the protocol
  (no direct filesystem access from the UI, P9).
- Governed by **[[09-planning]]** (when/what to ask — §3 materiality; do not ask unnecessary questions)
  and **[[10-risk-engine]]** (what counts as consequential and thus needs approval).
- **Assumption — single human:** exactly one user answers; no contention between responders. If this
  becomes multi-user, id-scoping and authorization must be revisited.
- **Assumption — a streaming channel exists:** the chat surface already streams (SSE today); this
  feature assumes an async push channel is available. The concrete transport is a `plan.md` decision.
- **Assumption — the agent proposes good, distinct options:** option *quality* (genuinely different
  2–4 proposals) is a behavioral expectation of the agent/persona, not something this channel enforces
  beyond the count bounds (FR-6).

## Acceptance Criteria

- [x] **AC-1:** During a task the backend can stream an Interaction Request to the frontend and pause
  the gated work until a matching response or timeout; the frontend renders it before the turn ends.
  (FR-1, FR-2)
- [x] **AC-2:** An **approval** request shows exactly one proposal with **Yes/No** plus **"chat about
  it"**; **Yes** proceeds, **No** does not, and neither is inferred without an explicit click.
  (FR-4, FR-6, FR-14)
- [x] **AC-3:** A **clarification** request shows **2–4** single-select proposals plus **"chat about
  it"**; selecting exactly one causes the agent to continue with that choice; a request with 0, 1, or
  >4 proposals is rejected as malformed. (FR-5, FR-6)
- [x] **AC-4:** Selecting **"chat about it"** opens a discussion **scoped to that interaction** without
  resolving it; afterward the user can still select/approve, and the agent may re-present an updated
  interaction. (FR-7)
- [x] **AC-5:** Typing in the **bottom chat box** while an interaction is pending starts a **new task**
  and does **not** answer the pending interaction, which remains answerable. (FR-8)
- [x] **AC-6:** Every request carries a timeout defaulting to **30s** and configurable; on expiry a
  notification auto-dismisses and a blocking request resolves to **no authorization** (nothing
  consequential runs) and reports **"Something goes wrong, please retry later"**; remaining time is
  visible and the countdown pauses during "chat about it". (FR-9, FR-14, D6, D8)
- [x] **AC-7:** Approval and clarification render as a **visually distinct card** (progress/countdown +
  selectable options + "chat about it") **as an assistant message inside the conversation scroll** (part
  of the message history; the human's selection appears as a user message), clearly marking that input is
  required. (FR-10)
- [x] **AC-8:** A pending interaction is **recoverable after reload/restart** and can be re-rendered and
  answered; the durable record is authoritative. (FR-11, P1)
- [x] **AC-9:** The interaction request/response protocol works over **REST** for a machine caller with
  effect equivalent to a UI click, verified by a parity check. (FR-12, P9)
- [x] **AC-10:** Each interaction (request, options, resolution/timeout, and any "chat about it" turns)
  is recorded in the conversation's `sessions/` record. (FR-13, P6)
- [x] **AC-11:** Responding to an **unknown/resolved/expired** interaction id is rejected with **no
  side effects** — no double execution, no post-timeout execution. (FR-16)
- [x] **AC-12:** At most **one blocking** interaction is outstanding per task and gated work does not
  proceed while it is; notifications may stream alongside. (FR-15)
- [x] **AC-13:** A consequential request's plan-first approval ([[002-assistant-chat]] FR-5) is
  delivered as an **approval** interaction, preserving "plan shown → explicit approval → execute"
  (P8). (FR-17)
- [x] **AC-14:** The agent can raise a **clarification** or **notification** on its own during a routine
  turn (via a workspace/conversation-bound tool); a clarification it raises pauses the turn and is
  surfaced as the turn's interaction, is durable (FR-11) and honors one-blocking-at-a-time (FR-15). The
  agent cannot self-**grant** an **approval** — it may request one through the governed channel, but the
  outcome comes only from the human or the operator's trust mode. (FR-18 as amended by
  [[010-agent-approval-channel]] FR-1/FR-2)

## Resolved Decisions

- **D1 — Approval is a 1-option clarification.** One protocol, one card, one response channel; approval
  is the degenerate (single-proposal, yes/no) case. *(User decision.)*
- **D2 — Option bounds: approval = 1, clarification = 2–4**, always plus a constant "chat about it".
  Single-select (radio), never multi-select. *(User decision.)*
- **D3 — "Chat about it" is always present** on approval/clarification and enters a context scoped to
  the pending interaction; it never resolves the interaction by itself. *(User decision.)*
- **D4 — Bottom chat box = new task.** The global chat box always starts a new top-level turn; deep
  context for a pending decision is entered only via the card. *(User decision.)*
- **D5 — Default timeout 30s, configurable**, with a visible animated countdown. *(User decision.)*
- **D6 — Timeout/decline is never authorization; timeout aborts with a fixed message.** A blocking
  interaction that times out or is declined performs no consequential action (safe default), preserving
  P8. On timeout the interaction **aborts** (no auto-select of any option) and the user is told
  **"Something goes wrong, please retry later"**. *(Derived from P8; message per user decision.)*
- **D7 — Async + durable delivery.** The request is streamed and the pending interaction is durable
  (survives reload/restart), reusing the conversation-store guarantees of [[002-assistant-chat]]
  FR-13/FR-14. *(Design decision.)*
- **D8 — Countdown pauses during "chat about it" and resets afterward.** Entering the card's deep-context
  discussion pauses the timeout; a re-presented interaction starts a fresh countdown. *(User decision.)*
- **D9 — Re-presented interaction gets a new id.** After "chat about it", an updated interaction is a
  new id that supersedes the prior one; responding to the superseded id is rejected (FR-16). *(User
  decision.)*
- **D10 — Notifications never block.** A notification always auto-expires and never requires
  acknowledgement. *(Confirmed; was an open question.)*
- **D11 — The countdown auto-expire is idempotent and reads only the live card.** The client-side timer
  fires the expire action at most once per interaction and seeds its remaining time from the currently
  active card alone (a resolved/superseded card carries no countdown), so a stale or zero-valued timer
  can never re-arm and drive an expire→re-render→expire loop. *(Bug fix: previously the timer could
  synchronously re-fire off a stale seed, causing a UI flip.)*

## Open Questions

- **Resolved in [`plan.md`](plan.md) (how, not what):** the push transport (turn-boundary SSE over the
  existing chat stream, not WebSocket), the on-disk shape of a pending interaction (a mutable
  `pending-interaction` frontmatter field in `sessions/<id>.md`), the REST endpoint shapes
  (`GET`/`POST /api/chat/interaction`, `POST /api/chat/interaction/stream`), and the card
  markup/animation (a distinct Gradio card with radio options + a client-side countdown wheel).

## Review Checklist

- [ ] No implementation details (how) leaked into this spec.
- [ ] Every requirement is testable.
- [ ] Scenarios cover the golden path and key edge cases.
- [ ] Complies with `memory/constitution.md`.
- [ ] Any local↔remote conflict captured in a `*-contradiction.md`, not silently resolved.
