# Feature Specification: Approval & Clarification Optimization (low-friction, effect-based gating)

**Feature ID:** `009-approval-optimization`
**Status:** Implemented
**Created:** 2026-08-27 · **Last Updated:** 2026-08-27

> Describes **what** and **why**. Reworks the human-in-the-loop model so the assistant is **fast and
> low-friction** — it **asks only when it truly matters**, never blocks on the *words* in a request,
> and **never asks for an approval it cannot honor**. Adds an operator **escape hatch** (auto-approve /
> trust mode) that can be passed per request and persisted so it applies to every request.
> Primary spec references: [[09-planning]], [[10-risk-engine]], [[13-api]], [[14-chat]],
> [[18-security]], and feature [[008-agent-user-interaction]]. Amends Constitution **P8** and aligns
> the code with **P12**.

## Problem (why this feature exists)

The current chat approval model (in `app/capabilities.py`) creates friction with no payoff. Three
root causes, all observable today:

1. **The gate fires on words, not effects.** `_CONSEQUENTIAL` is a regex over the **user's message**
   (`delete|remove|drop|overwrite|rewrite|merge|deploy|push|migrate|rename|create`). Harmless
   requests — "create a summary", "merge these two ideas", "rename this concept" — are blocked
   plan-first even though no state is mutated. It classifies **intent-words**, not **side-effects**.
   This directly contradicts **P12**, which requires risk to be evaluated by rules **declared as
   data**, not hard-coded lexical branches.

2. **The plan is fake.** `plan()` returns the same four boilerplate steps ("Clarify scope / Draft /
   Evaluate risk / Commit") for every request. Nothing about the approval describes what will
   actually happen, so the review is meaningless.

3. **Approval leads to a dead-end.** `_execute_pending` can only actually perform **two** actions —
   create a workspace, import a skill. Everything else returns *"Approved, but this action type isn't
   automatable yet in this build; the plan remains pending for a future capability."* The gate guards
   a capability that **does not exist** — the user is asked to approve, approves, and then learns it
   was never possible. Pure friction, zero payoff.

Compounding this, there are **two overlapping human-in-the-loop mechanisms** — deterministic
plan-first approval (P8) and agent-raised clarification cards ([[008-agent-user-interaction]] FR-18)
— and approval is delivered **as** an interaction card, blurring the line the constitution draws
(the agent must never manufacture its own consent gate).

**Core insight:** gate on **real, implemented effects at the capability boundary** — and **never ask
for an approval you can't honor**.

## Summary

Replace message-keyword gating with **effect-based gating at the capability boundary**:

- Every capability the chat/agent can invoke declares **effect metadata** (a data-declared rule set,
  P12): whether it is **executable** in this build and its **effect tier** — `auto`, `reversible`,
  or `approval`.
- A turn is gated **only** when an **executable** capability of tier `approval` is about to run.
  `auto` and `reversible` capabilities run immediately (reversible ones are git-committed, so they
  are one-command undoable). The user is interrupted **only when it truly matters**.
- If a request maps to **no executable action**, the turn is a **normal answer** — the assistant
  explains or advises. There is **no plan, no approval prompt, and no "not automatable" dead-end**.
- An **escape hatch** — `auto_approve` (a.k.a. **trust mode**) — can be passed **per request** and
  **persisted** so the UI selects it once and it rides **every** request. When on, `approval`-tier
  actions execute without prompting; everything stays **logged and git-committed** (auditable,
  reversible — P12 preserved).
- **Approval stays deterministic**: only the capability layer can raise an approval gate; the agent
  can raise **clarification/notification** cards but **never** approval (008 invariant preserved).
- Plans become **real**: an approval names the actual capability, its target, effect tier, and
  reversibility — so a review is informative.

## Goals

- **Speed & low friction by default.** Routine and reversible work runs without prompts; the operator
  is asked **only for genuinely consequential, executable, hard-to-undo actions**.
- **No false gates.** The gate never triggers on the wording of a request — only on a real effect
  about to occur.
- **No dead-ends.** The system never asks for an approval it cannot execute; non-executable intent
  degrades to a helpful answer.
- **Operator escape hatch.** A single, explicit **auto-approve/trust** control the operator can pass
  per request and **persist** so it applies to all requests, with an obvious way to turn it off.
- **Auditability preserved.** Every executed mutation — gated or auto-approved — is recorded in
  `log.md` and committed to the workspace's git repo (P12), so anything can be reviewed and reverted.
- **Constitutional alignment.** Bring the risk classification in line with **P12** (rules as data)
  and amend **P8** to recognize operator-granted standing consent.

## Non-Goals

- No new *mutating* capabilities are added by this feature (it does not implement "delete page",
  "deploy", etc.). It fixes **when and how** existing/future capabilities are gated, not the catalog
  of actions. New executable actions land in their own features and simply declare their tier.
- No change to the `vault/raw/` write-guard (P2) — raw remains create-only via the sanctioned capture
  channel; that guard is orthogonal to this gating model.
- No multi-user roles or per-user permissions — trust mode is a single-operator, machine-local
  setting.
- No removal of the interaction-card surface ([[008-agent-user-interaction]]); clarification and
  notification cards are unchanged. Only the **approval** path is reworked.
- No auto-merge of risky git branches without policy satisfaction (P12) — trust mode grants approval,
  it does not disable logging, committing, or branch policy.

## User Scenarios

- **Scenario 1 — Harmless "trigger word", no gate:** As a user, I say *"create a short summary of the
  auth concept"* or *"merge these two ideas into one note"*. The assistant just does it (or answers)
  — **no approval prompt**, because nothing destructive or non-executable is involved.
- **Scenario 2 — Reversible mutation runs, stays undoable:** As a user, I ask to add or edit a
  `vault/wiki/` page. It happens immediately and is **git-committed**; if I don't like it, one revert
  undoes it. I was not interrupted for a reversible change.
- **Scenario 3 — Genuinely consequential action asks once:** As a user, I ask for something
  destructive/irreversible or external (e.g. deleting a page, an external PM action). I get a **real
  plan** naming the exact action and its effect, and I approve **once** to proceed. This is the only
  case that interrupts me.
- **Scenario 4 — No dead-ends:** As a user, I ask for something this build can't perform (e.g.
  *"deploy to prod"*). I get a **straight answer** — "this build has no deploy action; here's how
  you'd do it" — **not** a plan I approve only to be told it was never possible.
- **Scenario 5 — Turn on trust mode for a fast session:** As a user, I open the settings quick menu
  and switch **Auto-approve** on. From then on every request carries it, so consequential actions run
  without prompting — while still being logged and committed. I can switch it off anytime; the setting
  **persists** across restarts until I do.
- **Scenario 6 — One-off override:** As a user (or an API client), I pass `auto_approve: true` on a
  single request to run that one consequential action without prompting, regardless of the persisted
  default; and `auto_approve: false` to force a prompt even when trust mode is on.
- **Scenario 7 — The agent still can't self-approve:** As the operator, I trust that the agent may
  ask me to **clarify** an ambiguous request (008 FR-18), but it can **never** grant its own approval
  for a consequential action — that gate is always deterministic and, when bypassed, bypassed only by
  **my** explicit auto-approve setting.

## Functional Requirements

### Effect-based gating (replaces keyword classification)

- **FR-1 (capability effect metadata):** Every capability invokable from a chat turn (directly or as
  an agent tool) MUST declare, as **data**, (a) whether it is **executable** in this build and (b) an
  **effect tier** ∈ {`auto`, `reversible`, `approval`}. These declarations are the risk rules and MUST
  be a data table, not hard-coded control flow (**P12**).
  - `auto` — reads and bookkeeping (e.g. `query`, `lint`, `spec_read`): run silently.
  - `reversible` — mutations that are fully recoverable via git (e.g. create/edit a `vault/wiki/`
    page, ingest): run **without a prompt** but **always** commit to git so they are undoable.
  - `approval` — destructive, irreversible-outside-git, or external effects: **gated** (see FR-3).
- **FR-2 (no message-keyword gating):** The `_CONSEQUENTIAL` regex over the user's message MUST be
  **removed**. Whether a turn is gated MUST depend on the **effect tier of the executable capability
  about to run**, never on words present in the request.
- **FR-3 (gate only executable approval-tier actions):** An approval prompt MUST be raised **only**
  when an **executable** capability of tier `approval` is about to run (and trust mode is off — FR-7).
  No other condition raises an approval prompt.
- **FR-4 (never gate a non-executable action):** If a request maps to **no executable capability**,
  the turn MUST proceed as a **normal answer** (explain/advise). It MUST NOT produce a plan, an
  approval prompt, or the "not automatable yet" message. The dead-end branch in `_execute_pending`
  MUST be removed; an approval is only ever created when a real executor exists.
- **FR-5 (real plans):** When an approval is raised, the plan MUST describe the **actual** action(s)
  — the capability name, its target (workspace/page/etc.), its effect tier, and its reversibility —
  not generic boilerplate. The approved plan MUST execute that exact action on approval.
- **FR-6 (auditability):** Every executed mutation — whether it ran as `reversible`, was approved, or
  was auto-approved (FR-7) — MUST be recorded in `log.md` and committed to the workspace's git repo,
  so any change is reviewable and revertible (**P12**).

### Escape hatch (auto-approve / trust mode)

- **FR-7 (per-request auto-approve):** A boolean **`auto_approve`** parameter MUST be accepted on the
  chat request (`ChatRequest`) and on the REST surface for consequential work. When true, an action
  that would otherwise be gated at tier `approval` (FR-3) MUST execute **without prompting**, still
  honoring FR-6 (log + commit).
- **FR-8 (persisted trust mode):** The operator's `auto_approve` preference MUST be **persistable**
  (stored in the runtime settings file, alongside the selected model — `LEADER_SETTINGS_PATH`) and
  MUST be exposed over REST for read and update (parity with the model endpoints, **P9**). Once set,
  it applies to **every** request that does not override it.
- **FR-9 (precedence):** An **explicit per-request** `auto_approve` MUST override the persisted
  default **for that turn only** (both directions: `true` forces auto-approve even if the stored
  default is off; `false` forces a prompt even if the stored default is on). Absent the per-request
  value, the persisted default applies.
- **FR-10 (UI control):** The web UI MUST expose an **Auto-approve** toggle in the settings quick
  menu (the extensible shell from [[004-assistant-sidebar]] FR-35), reflecting and updating the
  persisted setting over `/api/*` only (**P9**), and passing the value on requests. The current state
  MUST be visible so the operator always knows whether trust mode is on.
- **FR-11 (trust mode is operator-only):** `auto_approve` MUST be settable **only** by the operator
  (request parameter or persisted setting). The **agent MUST NOT** be able to set, read-to-bypass, or
  otherwise self-grant it. (Preserves the 008 invariant: the agent can raise clarification/notification
  but never approval.)

### Human-in-the-loop model (deterministic approval, separate from clarification)

- **FR-12 (deterministic approval only):** Approval interactions/gates MUST be produced **only** by
  the capability layer, never by the agent. Clarification and notification cards remain agent-raised
  ([[008-agent-user-interaction]] FR-18) and are **unchanged**. The two kinds MUST stay on distinct
  code paths and be distinguishable to the UI.
- **FR-13 (approve/execute integrity):** Approving a pending plan MUST execute the **exact** stored
  action (FR-5) and then clear the pending plan and its shadow approval interaction. If (and only if)
  no executor exists for a stored plan, that is a bug — FR-4 guarantees such a plan is never created.

## Acceptance Criteria

- [x] **AC-1:** A message containing a former trigger word but no real effect (e.g. "create a
  summary", "merge these ideas", "rename this concept") produces **no approval prompt**. (FR-2, FR-3)
- [x] **AC-2:** `auto`/`reversible` capabilities run **without a prompt**; a `reversible` mutation is
  **git-committed** and appears in `log.md`. (FR-1, FR-6)
- [x] **AC-3:** An **executable** `approval`-tier action (trust off) raises a **real** plan naming the
  action + target + reversibility, and approving it executes that exact action. (FR-3, FR-5, FR-13)
- [x] **AC-4:** A request with **no executable capability** returns a normal answer — **no plan, no
  approval, and the string "isn't automatable yet" never appears**. (FR-4)
- [x] **AC-5:** With `auto_approve: true` (per request), an `approval`-tier action executes without a
  prompt and is logged + committed. (FR-7, FR-6)
- [x] **AC-6:** The persisted trust setting is readable/updatable over REST and survives a restart;
  when on, requests without an explicit override are auto-approved. (FR-8)
- [x] **AC-7:** Per-request `auto_approve` overrides the persisted default both ways (true forces
  auto; false forces a prompt). (FR-9)
- [x] **AC-8:** The UI settings quick menu shows and toggles Auto-approve, reads/writes it only over
  `/api/*`, and reflects the persisted state. (FR-10, P9)
- [x] **AC-9:** The agent cannot set or bypass `auto_approve`, and cannot raise an approval card; it
  can still raise clarification/notification cards. (FR-11, FR-12)
- [x] **AC-10:** The `_CONSEQUENTIAL` message regex is gone; risk is decided from data-declared
  capability tiers. (FR-1, FR-2, P12)

## Key Decisions

- **D1 — Gate at the boundary, on effects.** Risk is a property of the **capability about to run**,
  declared as data (P12), evaluated at the moment of execution — not inferred from the user's phrasing.
  This is the single change that removes false gates.
- **D2 — Three tiers, git as the safety net.** `reversible` mutations run freely because git makes
  them undoable; only `approval`-tier (destructive/irreversible/external) interrupts. This is the
  concrete meaning of "ask only when it truly matters."
- **D3 — Non-executable ⇒ answer, not gate.** The dead-end message is deleted. An approval is created
  **only** when an executor exists, so approving always accomplishes something.
- **D4 — Escape hatch is explicit, persisted, operator-only.** `auto_approve` is standing consent the
  **human** grants; the agent can never touch it. Auditability (log + git) is retained even when it's
  on, so "human in control" holds via review/revert rather than per-action prompts.
- **D5 — Keep approval deterministic; keep clarification agent-driven.** Two distinct paths; the
  approval gate is un-fakeable by the agent (preserves the 008 invariant).

## Constitution impact (must precede implementation)

- **P12 (risk-governed mutations):** No conflict — this feature **implements** P12 as written
  (rules as data, auditable in `log.md`) and **removes** the non-compliant hard-coded regex.
- **P8 (human-in-the-loop):** Requires a **PATCH/MINOR amendment**. Today P8 reads that consequential
  work "requires a plan the user can review before execution." This feature introduces **operator-set
  standing consent** (auto-approve). The amendment MUST state that P8 is satisfied when the human
  either (a) reviews a per-action plan, **or** (b) has **explicitly and deliberately** granted
  standing consent via trust mode, provided every action remains **logged and git-reverting**
  (auditable after the fact). The agent still cannot self-approve. Bump the constitution version and
  record the amendment before code changes (per `CLAUDE.md` workflow step 1).

## Downstream specs to reconcile

- [[09-planning]] — planning is invoked for **executable approval-tier** work only; plans are concrete
  (FR-5), not boilerplate.
- [[10-risk-engine]] — the effect-tier table is the risk rule set (data-declared); document tiers and
  the `auto_approve` bypass.
- [[13-api]] — add `auto_approve` to the consequential request contract and a settings read/update
  endpoint (parity with `/api/models`).
- [[14-chat]] — `ChatRequest` gains `auto_approve`; document the low-friction turn flow.
- [[008-agent-user-interaction]] — clarify that **approval** cards are capability-layer-only and
  distinct from agent clarification/notification (FR-12).

## Implementation note (follow-up, not this document)

Per `CLAUDE.md` (spec → code → tests): after this spec and the P8 amendment are accepted, implement in
`app/capabilities.py` (effect table + boundary gate, delete `_CONSEQUENTIAL`, delete the dead-end
branch, real `plan()`), `app/models.py` (`auto_approve` on `ChatRequest`; settings shape),
`app/api.py` (settings read/update endpoint; accept `auto_approve`), `app/agent.py` (tools carry
effect tiers; agent cannot set `auto_approve`), and `app/ui.py` (Auto-approve toggle in the settings
quick menu). Land tests mapping to AC-1…AC-10 in the same change.
