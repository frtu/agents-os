# Feature Specification: Agent Approval Channel (ask structurally, grant deterministically)

**Feature ID:** `010-agent-approval-channel`
**Status:** Implemented
**Created:** 2026-08-28 · **Last Updated:** 2026-08-28

> Describes **what** and **why**. Gives the agent a **structured way to ask** for consent, while
> keeping the **granting** of consent deterministic and human-owned. Trust mode
> ([[009-approval-optimization]]) then answers those requests **on the operator's behalf, in the same
> turn**, so an approved workflow runs to completion instead of stopping mid-way.
> Primary spec references: [[008-agent-user-interaction]], [[009-approval-optimization]],
> [[09-planning]], [[13-api]], [[14-chat]]. Amends 008 **FR-18** and 009 **FR-12**.

## Problem (why this feature exists)

Feature 009 made gating **effect-based** and added trust mode, but it only governs the
**deterministic** gate — the capability layer's `_resolve_action` → `EFFECTS[...].tier == "approval"`
path. The agent's own judgment about what deserves consent is not covered, and the agent has no
approval channel at all: [[008-agent-user-interaction]] FR-18 forbids it from raising an approval, and
the persona guardrail tells it "approval always comes from the user".

Observed in workspace `search-catalog`, session `1e0d259bf2f3.md` — the agent's *evaluation* was
excellent (it recognised installing 9 skills is approval-tier per 009, enumerated every skill, named
the effect and the reversibility, and refused to act) — but it had to deliver that judgment as
**prose**: *"Reply **approve** (or 'go ahead') and I'll import them one by one."* The user then typed
`approve` as an ordinary chat message and the work proceeded.

Three problems follow from the approval being prose rather than protocol:

1. **Trust mode cannot skip it.** `auto_approve` never sees this request, because nothing structured
   was raised. The operator switches trust mode on and is *still* stopped and asked — the escape hatch
   does not cover the case it is most needed for.
2. **It is invisible to the protocol.** A prose approval has no interaction id, no countdown, no
   durable `pending-interaction` record, and no resolution event. It cannot be re-presented after a
   reload, cannot time out to a safe default, and does not appear in the audit trail as a consent
   event — all guarantees [[008-agent-user-interaction]] exists to provide.
3. **The invariant leaks anyway.** 008 FR-18 says the agent must not self-initiate an approval, yet in
   practice it does — just through the one channel the protocol cannot see or govern. Forbidding the
   *structured* form only guarantees the *unstructured* form.

**Core insight:** the invariant worth protecting is **who grants consent**, not **who asks**. The
agent asking "may I?" through a governed channel does not weaken human control — it strengthens it,
because the request becomes visible, durable, timeout-bounded, auditable, and answerable by the
operator's standing consent.

## Summary

Split *asking* from *granting*:

- The agent gets a **`request_approval` tool**. It states what it wants to do and why; it can never
  answer its own request.
- The **capability layer decides the outcome**, exactly as it does for the deterministic gate:
  - **Trust mode OFF (default)** — a real **blocking approval card** is raised (the existing 008
    protocol: one proposal, "chat about it", decline, countdown, durable record). The tool tells the
    agent to **stop and wait**. The human makes the final decision.
  - **Trust mode ON** — the layer answers **"approved" on the operator's behalf immediately**,
    in-turn. The tool returns the grant, the agent **continues through its intermediate step into
    final execution**, and the approval is surfaced to the frontend as **inert, already-decided
    context** so the operator can see what was authorised for them.
- Either way the consent event is **logged** (`log.md` + the session record), so P8 holds through
  review-and-revert when it did not hold through a prompt.
- Answering an approval **resumes the turn**, so the agent finishes the work it asked about instead of
  ending the turn with an acknowledgement.

## Goals

- **Trust mode actually skips every approval**, including ones the agent raises on its own judgment.
- **No prose approvals.** A consent request is always a protocol object: id, options, countdown,
  durable record, resolution event.
- **Human makes the final decision by default.** Trust mode is off unless the operator turns it on;
  with it off, behaviour is strictly better than today (a card instead of a prose instruction).
- **No dead-ends** ([[009-approval-optimization]] D3 extended): approving resumes the work.
- **Visible delegation.** When the backend decides on the operator's behalf, the operator can see
  that it happened, and what it covered.
- **The agent still cannot self-grant.** Asking is agent-initiable; granting never is.

## Non-Goals

- No new *mutating* capabilities (unchanged from 009). This governs how consent is requested and
  granted, not what can be done.
- **Clarification is not auto-answered.** Trust mode grants *consent*; it does not invent *choices*.
  An agent-raised clarification ([[008-agent-user-interaction]] FR-18) still blocks for the human even
  when trust mode is on, because picking one of several distinct approaches is not something standing
  consent can express.
- No change to `vault/raw/` immutability (P2) or to the effect-tier table (009 FR-1).
- No per-tool or per-capability trust granularity — trust mode stays a single operator-level switch.

## User Scenarios

- **Scenario 1 — Default: the human decides (trust OFF):** As a user, I ask to install 9 skills. The
  agent raises an **approval card** naming exactly what it will do; nothing runs. I click approve and
  the agent **continues in the same thread** and installs them. (Previously: a prose "reply approve",
  and my reply started a fresh turn.)
- **Scenario 2 — Trust ON: it decides for me and continues:** As a user with Auto-approve on, I ask
  the same thing. The agent asks internally, the backend answers **approved** on my behalf, and the
  installation completes in **one turn**. Below the reply I can see an inert card recording *what* was
  auto-approved.
- **Scenario 3 — I can always see the mode:** As a user, a line under the chat input tells me whether
  Auto-approve is on, so I am never surprised that a consequential action ran without asking.
- **Scenario 4 — Declining still stops everything:** As a user, I decline the card (or let it time
  out). No action runs and the agent is told so.
- **Scenario 5 — The agent still cannot self-approve:** As the operator, the agent may *ask* for
  consent, but the answer comes only from me or from trust mode **I** enabled. It has no tool to read,
  set, or bypass trust mode, and no way to answer its own request.

## Functional Requirements

### The approval channel

- **FR-1 (agent approval requests):** The agent MUST have a tool to **request** approval for work it
  judges consequential, stating what it intends to do. The request MUST become a protocol
  **Interaction** of kind `approval` ([[008-agent-user-interaction]] FR-4: exactly one proposal), with
  an id, a durable record when blocking, and a resolution event — never prose.
- **FR-2 (the agent never grants):** The **outcome** of an approval request MUST be decided by the
  capability layer alone — from the human's answer or the operator's persisted/per-request trust mode.
  The agent MUST NOT be able to answer its own request, and MUST have no tool to read, set, or bypass
  trust mode ([[009-approval-optimization]] FR-11 unchanged).
- **FR-3 (trust OFF → block and ask):** With trust mode off, an approval request MUST raise a
  **blocking approval card** and the tool result MUST instruct the agent to **stop and take no
  action** until answered. The full 008 protocol applies: the constant "chat about it" affordance
  (FR-7), decline, one-blocking-at-a-time (FR-15), timeout to the safe default (FR-9), durability
  across reload (FR-11).
- **FR-4 (trust ON → grant in-turn and continue):** With trust mode on, the layer MUST resolve the
  request as **approved on the operator's behalf immediately**, without a round trip. The tool result
  MUST tell the agent it is authorised to proceed, so it **continues its intermediate step through to
  final execution within the same turn**.
- **FR-5 (auto-approved context is surfaced):** An approval granted under FR-4 MUST be reported to the
  frontend as **already-decided context** — an interaction with `status="resolved"` and
  `resolution="auto-approved"` — so the surface can display what was authorised without offering
  options. It MUST NOT be presented as answerable, MUST NOT block, and MUST NOT be stored as a pending
  interaction.
- **FR-6 (consent is always audited):** Every approval outcome — human-granted, auto-granted,
  declined, or expired — MUST be recorded in the conversation's session record, and an auto-granted one
  MUST additionally be appended to the workspace's `vault/wiki/log.md`. Standing consent replaces the
  prompt, never the audit trail (**P8** v1.2.0, **P12**).
- **FR-7 (answering resumes the work):** Selecting an option on an agent-raised approval or
  clarification MUST **resume the turn** so the agent completes the work it asked about. Acknowledging
  the choice without continuing (today's *"Proceeding with your choice: X."*) is a dead-end and MUST
  be replaced. Decline and timeout MUST continue to run nothing (FR-3).
- **FR-8 (clarification is unaffected):** Trust mode MUST NOT auto-answer a **clarification**; it
  blocks for the human regardless. Approval and clarification MUST stay distinguishable to every
  surface ([[009-approval-optimization]] FR-12 as amended below).

### Operator visibility

- **FR-9 (persistent mode indicator):** The web UI MUST display the current Auto-approve state in a
  **persistent line beneath the chat input row**, visible without opening the settings menu, and it
  MUST update immediately when the toggle changes ([[009-approval-optimization]] FR-10 refined: the
  state line moves out of the popover so it is always in view).
- **FR-10 (the toggle stays where it is):** The Auto-approve control remains a sub-panel of the
  settings quick menu opened by the **⚙ button beside Submit**, reading and writing the persisted
  setting over `/api/settings` only (**P9**), and riding every chat request.

## Amendments to existing specs (must precede implementation)

- **[[008-agent-user-interaction]] FR-18** currently: *"The agent MUST NOT self-initiate an
  **approval**: authorization … stays with the deterministic plan-first path … so the agent cannot
  manufacture its own consent gate."* **Amended to:** the agent MAY **request** an approval through
  the governed channel (FR-1); it MUST NOT **grant** one (FR-2). The rationale is preserved verbatim —
  the agent cannot manufacture its own *consent* — and strengthened, because the alternative it was
  driving the model toward was an ungoverned prose approval.
- **[[009-approval-optimization]] FR-12** currently: *"Approval interactions/gates MUST be produced
  **only** by the capability layer, never by the agent."* **Amended to:** approval **outcomes** are
  produced only by the capability layer; approval **requests** may originate from the deterministic
  plan-first path or from the agent (FR-1/FR-2). The two-distinct-paths requirement is unchanged.

Neither amendment touches the **Constitution**: **P8** (v1.2.0) already recognises standing consent,
and **P12** is satisfied by FR-6. Who is in control does not change — only who is allowed to ask.

## Acceptance Criteria

- [x] **AC-1:** With trust mode off, an agent approval request raises a blocking `approval` interaction
  with exactly one proposal, persists it as the pending record, and the tool result tells the agent to
  stop and take no action. Nothing is mutated that turn. (FR-1, FR-3)
- [x] **AC-2:** With trust mode on, the same request is resolved immediately as approved, the tool
  result authorises the agent to proceed, and no blocking card is stored or presented. (FR-4)
- [x] **AC-3:** An auto-granted approval reaches the frontend with `status="resolved"` and
  `resolution="auto-approved"`, and the UI renders it as an inert card with no selectable options.
  (FR-5)
- [x] **AC-4:** An auto-granted approval appends an entry to `vault/wiki/log.md` and to the session
  record; a human-granted, declined, or expired one is recorded in the session record. (FR-6)
- [x] **AC-5:** Approving an agent-raised approval resumes the turn and the agent completes the
  requested work; the reply is not a bare "Proceeding with your choice". (FR-7)
- [x] **AC-6:** Declining or letting an agent-raised approval expire runs no action. (FR-3)
- [x] **AC-7:** A clarification is never auto-answered — with trust mode on it still blocks for the
  human. (FR-8)
- [x] **AC-8:** The agent has no tool to grant an approval, answer an interaction, or read/set trust
  mode; `request_interaction` still rejects `kind="approval"`. (FR-2)
- [x] **AC-9:** The persisted trust state is rendered in a line below the chat input row and updates
  when toggled, reading only `/api/*`. (FR-9, FR-10, P9)
- [x] **AC-10:** A per-request `auto_approve` override decides an agent-raised approval the same way it
  decides a deterministic one, in both directions ([[009-approval-optimization]] FR-9 preserved).

## Key Decisions

- **D1 — Ask ≠ grant.** The whole feature is this split. Asking is a capability the agent needs to do
  its job well; granting is the operator's. Conflating them is what forced the model into prose.
- **D2 — Prose approval is a protocol failure, not a style problem.** Any approval the protocol cannot
  see is one trust mode cannot skip, the UI cannot re-present, and the audit trail cannot record. The
  tool exists so the request is always a governed object.
- **D3 — Trust mode answers, it does not silence.** With trust on, the request is still created,
  resolved, logged, and surfaced as context (FR-5/FR-6) — the operator loses the prompt, not the
  visibility. This is what keeps P8 satisfied by review-and-revert.
- **D4 — Consent is delegable; choice is not.** Standing consent can say "yes, proceed" in advance. It
  cannot say which of four approaches the operator prefers, so clarification stays blocking (FR-8).
- **D5 — Answering resumes the turn.** An approval whose grant does not continue the work is the same
  dead-end 009 D3 removed, one layer up.

## Downstream specs to reconcile

- [[008-agent-user-interaction]] — FR-18 amended (agent may request, not grant); FR-16's "resume the
  task" is now actually implemented for option selection (FR-7).
- [[009-approval-optimization]] — FR-12 amended (outcomes vs requests); FR-10 refined by FR-9 (the
  state line moves below the input).
- [[13-api]] — the approval channel adds no route: it rides `ChatDelta.interaction` and the existing
  `/api/chat/interaction` endpoints. Document that a resolved+`auto-approved` interaction may appear
  there as context.
- [[14-chat]] — document the in-turn grant in the low-friction turn flow.
- [[09-planning]] — the agent's own judgment about what needs consent now has a governed channel;
  §3 (don't ask unnecessary questions) still applies to it.

## Implementation note (follow-up, not this document)

Per `CLAUDE.md` (spec → code → tests): `app/capabilities.py` (the approval-request capability, in-turn
grant, log entry, resume-on-select), `app/agent.py` (the `request_approval` tool, effective trust mode
threaded into the tool closures), `app/persona.py` (ask via the tool, never prose), `app/ui.py` (state
line below the input row; inert auto-approved card). Land tests mapping to AC-1…AC-10 in the same
change.
