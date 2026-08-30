# Feature Specification: Maker–Checker Approval (three independent layers: execute, report, judge)

**Feature ID:** `011-maker-checker-approval`
**Status:** Draft — governance amendments applied, implementation not started
**Created:** 2026-08-29 · **Last Updated:** 2026-08-29

> Describes **what** and **why**. Replaces the single-function approval gate with a **maker–checker**
> architecture of **three independent layers** — an **execution** layer that only does work, a
> **workflow reporting** layer that observes an entire user-triggered execution and accumulates a
> scored list of risky operations, and a **judge** layer that decides whether the operator must be
> asked. A **concierge** becomes the single entry point from any surface. The judge **learns**: every
> decision is captured as past experience so a shape the operator has already approved need not be
> asked again.
> Primary spec references: [[09-planning]], [[10-risk-engine]], [[12-assistant]], [[13-api]],
> [[14-chat]], [[18-security]], and features [[008-agent-user-interaction]],
> [[009-approval-optimization]], [[010-agent-approval-channel]].
> Amends Constitution **P8** (MAJOR — bounded delegation to a non-human checker), **P12**
> (rules-as-data extended to scoring modifiers), and supersedes 009 **FR-3** and 010 **FR-2**.

## Problem (why this feature exists)

1. **The "capability boundary" gate does not sit at the capability boundary.** `app/capabilities.py`
   documents an effect-based gate, but the decision is made by `_resolve_action(message)`
   (`app/capabilities.py:108-125`), which **regex-matches the user's message text** against a closed
   tuple of exactly two resolvers — `create_workspace` and `import_skill`
   (`_ACTION_RESOLVERS`, `app/capabilities.py:~100`). A message that matches neither has, by
   definition, "no executable effect" and is never gated. This is the very thing 009 FR-2 set out to
   remove; it was narrowed from a regex over risky *verbs* to a regex over two *action names*, but it
   is still a decision made on the wording of a request before any work happens.
2. **The overwhelming majority of real mutations are ungated.** Once past that gate, the turn is
   handed to the SDK runtime, which holds `["Skill", "Bash", "Read", "Write", "Edit", "Glob",
   "Grep"]` (`app/agent.py:38`) under `permission_mode="bypassPermissions"` (`app/agent.py:368`).
   The only enforcement is the `vault/raw/` PreToolUse hook (`app/agent.py:293-310`). Every write to
   `vault/wiki/`, every `Edit`, and every `Bash` command outside `vault/raw/` executes with no risk
   evaluation at all.
3. **The agent's approval channel is advisory, not enforcing.** `request_approval_h`
   (`app/agent.py:181-205`) returns *prose* on a not-approved outcome — "STOP here and take no
   action… do not use any mutating tool". Nothing prevents the model from proceeding anyway. The one
   mechanism that can actually deny a tool call is the PreToolUse hook, and it is not wired to
   approval.
4. **Risk is binary and per-action, never accumulated.** `Effect.tier` is one of
   `auto|reversible|approval` and the gate fires on a single resolved action. Nothing anywhere
   accumulates the set of risky operations a single user request will cause, so the operator is never
   shown the blast radius of what they are approving — only one action at a time.
5. **Deciding, scoring, executing and rendering are one function.** `ask_stream`
   (`app/capabilities.py:~1006-1048`) resolves the action, reads the effect tier, consults trust
   mode, builds the plan, writes the pending record, composes the reply, *and* builds the interaction
   card — inline, in one control flow. There is no seam at which the risk policy could be replaced
   without touching execution, and none at which execution could be replaced without touching the UI.
6. **Nothing is learned.** Every approval is asked as if for the first time. The operator's only
   lever is a global on/off `auto_approve`, so the choice is "ask me about everything" or "ask me
   about nothing" — with no middle ground informed by what they have already approved.

**Core insight:** approval is not a property of a *message*, nor of a single *action*. It is a
property of the **whole execution a request causes**, judged as a set. Making that judgeable requires
separating the thing that *acts* from the thing that *observes and scores* from the thing that
*decides* — and letting the deciding layer remember.

## Summary

Every user request, from any surface, enters through a **concierge**. The concierge opens a
**workflow run** and invokes execution. Execution performs work and announces each operation it is
about to attempt. The **reporting layer** scores each announced operation 1–5, records a one-line
justification of its effect, and accumulates them against the run. At the first operation whose score
reaches the gate threshold, execution **pauses** and the accumulated report — the objective, what has
already run, and what is now being attempted — goes to the **judge**.

The judge is an LLM risk agent. It reads the report plus the operator's hint (trust mode) and past
experience, and returns **approve**, **decline**, or **ask** with its reasoning. A deterministic
post-filter bounds it: an `approve` is honoured only under standing consent or a matching precedent;
otherwise it is downgraded to `ask`. When the operator answers, execution resumes synchronously from
the paused operation, and the decision is captured asynchronously as experience so the same shape can
be skipped next time.

## Goals

- Three layers that can each be developed, tested, replaced and reasoned about **alone**.
- Gate on the **actual operation about to run**, including the agent's native tools — never on
  message text.
- Show the operator an **accumulated, scored list** with justifications, not a single opaque action.
- **Enforce** a pause, rather than instructing a model to stop.
- Ask **less over time** by remembering what the operator already approved, without ever silently
  broadening consent.
- Keep one surface for asking (the 008 interaction card) and one entry point for calling.

## Non-Goals

- Not a permission-prompt UI for individual tools; the SDK's own permission model is out of scope
  except where the hook is used as the enforcement point.
- Not an attempt to make `Bash` statically analysable. Coarse detection plus git as backstop, as
  today (010 D3).
- Not automatic tuning of scoring weights. Suggested changes only; a human applies them.
- Not a replacement for the `vault/raw/` guard (P2), which remains an absolute prohibition
  independent of any score.
- Not cross-operator or multi-tenant trust. Experience belongs to the single local operator.

## User Scenarios

1. **Ungated work stays fast.** The operator asks a question. Execution reads pages, every operation
   scores 1, nothing reaches the threshold, no run is ever paused, and no card appears.
2. **Blast radius before consent.** The operator asks to reorganise the wiki. Execution rewrites
   three pages (score 2 each, reversible via git) and then attempts a delete (score 4). The run
   pauses and the card shows all four operations, each with its score and one-line effect, so the
   operator sees the delete *and* what already happened.
3. **Precedent skips the ask.** The operator has approved "import skill" four times. On the fifth,
   the judge matches the fingerprint, returns `approve`, the deterministic filter honours it, and the
   work completes without a card. The reply states it was auto-approved on precedent.
4. **Novel work still asks, even in trust mode.** Trust mode is on but the request would run a
   capability never seen before at score 5. The judge may approve under standing consent, but the
   card is still shown because the score exceeds the precedent-free ceiling.
5. **Cold start asks.** A fresh install has no experience records. Every gated operation asks,
   regardless of what the judge reasons.
6. **Decline is final.** The operator declines. The paused operation does not run, the run ends,
   nothing is retried, and no card for the same operation reappears in that run.
7. **A judge outage is safe.** The judge is unreachable. Every gated operation falls back to `ask`.
8. **Audit after the fact.** The operator opens the run record and sees each operation, its score,
   the modifiers that produced it, the judge's reasoning, who decided, and the resulting commit.

## Functional Requirements

### Layer 1 — execution (maker)

- **FR-1:** Layer 1 is the **only** layer that performs work: the capability functions plus the
  agent's tools. It continues to declare per-capability effect metadata (tier, reversibility,
  `executable`) as data.
- **FR-2:** Layer 1 MUST NOT compute a risk score, read past experience, consult trust mode, or
  decide anything about approval. It announces each operation it is about to attempt and honours the
  permit it receives.
- **FR-3:** The announce/permit contract MUST be a **single abstract interface** with one operation
  (`permit(operation) -> Permit`, where `Permit` is allow or deny-with-reason). A default
  implementation MUST allow everything, so layer 1 runs correctly with layers 2 and 3 absent.
- **FR-4:** For the agent's native tools the enforcement point MUST be the **PreToolUse hook**, whose
  `deny` is authoritative. Prose instructing a model to stop MUST NOT be relied on as a gate.
- **FR-5:** An operation announcement MUST carry enough to be judged without layer 1's help:
  capability-or-tool name, resolved target, declared tier, reversibility, and whether it is
  externally visible.

### Layer 2 — workflow reporting (maker)

- **FR-6:** Exactly one **workflow run** MUST be opened per user request, spanning the whole
  execution it causes — both capability calls and agent native tool calls.
- **FR-7:** Every announced operation MUST be recorded with: capability/tool, target, declared tier,
  **risk score 1–5**, the modifiers that produced it, a **one-line justification**, reversibility, and
  status (`pending` / `executed` / `declined` / `not-reached`).
- **FR-8:** The score MUST be derived as **base + modifiers**, clamped to 1–5. Base comes from the
  declared tier: `auto` = 1, `reversible` = 2, `approval` = 4. Modifiers MUST be **declared as data**
  (P12), each with a name, condition, weight and human-readable reason.
- **FR-9:** Modifiers MUST describe only the **operation's effect** — irreversibility outside git,
  breadth of change, external visibility, privilege granting, target sensitivity. A modifier MUST NOT
  reference trust mode, precedent, operator identity, or the request's wording; those belong to
  layer 3.
- **FR-10:** The justification MUST be one line stating the concrete effect and its undo path (e.g.
  "deletes 3 wiki pages; recoverable from the workspace git repo").
- **FR-11:** Layer 2 MUST **accumulate**. When an operation's score reaches the gate threshold, the
  report handed onward MUST include the gating operation **and** every operation already executed in
  the run, so the operator sees the full blast radius.
- **FR-12:** Layer 2 MUST pause at the **first** operation reaching the threshold, and MUST NOT
  continue executing past it while awaiting a verdict.
- **FR-13:** Layer 2 MUST NOT decide. It hands a report to a **single abstract checker interface**
  (`review(report) -> Verdict`) and applies whatever comes back. A default implementation MUST return
  `ask`, so layer 2 is correct with layer 3 absent.
- **FR-14:** The run record MUST be persisted for audit, including the verdict, its source, and the
  reasoning behind it.

### Layer 3 — judge / risk agent (checker)

- **FR-15:** The judge MUST receive the **objective** (the user's request), the accumulated risky
  operation list, the operations already executed, and the operator hint (trust mode), and MUST
  return one of `approve` / `decline` / `ask` with reasoning and a confidence.
- **FR-16:** The judge MAY be an **LLM risk agent** and its reasoning MUST be recorded verbatim as
  the audit justification for the decision.
- **FR-17: Bounded delegation.** A judge `approve` MUST be honoured only when **either** the operator
  has enabled standing consent (trust mode) **or** past experience holds a **matching precedent**
  meeting the configured minimum sample count with no operator decline in the window. Otherwise it
  MUST be downgraded to `ask`. This filter MUST be **deterministic code applied after** the judge
  returns — the judge cannot widen its own authority.
- **FR-18:** Even under standing consent, an operation scoring above the configured
  **precedent-free ceiling** MUST still `ask` when no matching precedent exists.
- **FR-19:** The judge MAY return `decline` autonomously **only** on precedent of a prior operator
  decline for the same fingerprint. With no such precedent it MUST return `ask`; it MUST NOT invent a
  refusal.
- **FR-20: Cold start.** With no experience records, every gated operation MUST resolve to `ask`,
  whatever the judge reasons.
- **FR-21: Fail closed.** An unavailable, timed-out, or malformed judge response MUST resolve to
  `ask`.
- **FR-22:** The judge MUST have **no execution capability** — no capability-layer access, no tools,
  no filesystem writes other than the experience store.

### Concierge / orchestrator

- **FR-23:** Every user→backend call MUST enter through the concierge, on **both** REST and chat
  (P9). No surface may reach execution directly.
- **FR-24:** The concierge owns the sequence and nothing else: open run → invoke execution → on pause
  consult the judge → surface an ask if required → resume on answer → record experience
  asynchronously.
- **FR-25:** An ask MUST surface as the existing **008 approval interaction card**. This feature adds
  no new asking surface and no new REST route for asking.
- **FR-26:** On operator approval, execution MUST **resume synchronously** and complete the paused
  operation within the same request/turn.
- **FR-27:** An operator decline MUST be **final** for that operation and run: it does not execute,
  the run terminates, and the same operation MUST NOT be re-asked within the run.

### Past experience

- **FR-28:** Experience MUST be an **append-only JSONL** file plus a separate **hand-editable JSON**
  of weights and thresholds, both at the workspace root alongside the existing settings file.
- **FR-29:** One record per decision, containing at least: timestamp, run id, objective fingerprint,
  operation fingerprint, score, band, decision, **source** (`user` / `judge` / `trust`), matched
  precedent id if any, and the execution outcome.
- **FR-30:** A record MUST be written after **every** decision — operator approve, operator decline,
  judge auto-approve, judge auto-decline — and the write MUST be **asynchronous** and MUST NOT block
  or fail the response.
- **FR-31:** The **operation fingerprint** MUST be deterministic, stable and human-auditable, so a
  precedent match can be explained without running the judge.
- **FR-32:** Weights and thresholds MUST be hand-editable and read fresh. A separate analysis routine
  MAY **suggest** updates from accumulated records but MUST NOT apply them automatically.
- **FR-33:** Experience is **global** across workspaces, because trust is a property of the operator,
  not of a workspace.

### Layer independence

- **FR-34:** No layer may import another's internals. Layer 1 MUST NOT import layers 2 or 3; layer 2
  MUST NOT import layer 3. All traffic goes through the FR-3 and FR-13 contracts as plain data.
- **FR-35:** Each layer MUST be independently testable with the other two replaced by the default
  stubs of FR-3 and FR-13.
- **FR-36:** The scoring model (layer 2) and the effect-tier model (layer 1) MUST remain separately
  evolvable: adding a modifier MUST NOT require an effect-table change, and adding a capability MUST
  NOT require a modifier change.

## Data & file contracts

```text
<workspace root>/.leader-experience.jsonl   append-only decision records (FR-28/FR-29)
<workspace root>/.leader-risk-weights.json  modifier weights, bands, thresholds (FR-28/FR-32)
<workspace>/vault/wiki/log.md               executed mutations, as today (P8)
```

```text
Operation   { op_id, kind: capability|tool, name, target, tier, reversibility,
              external, score 1-5, modifiers[], justification, status }
RiskReport  { run_id, objective, workspace, gating_op, accumulated[], executed[] }
Verdict     { decision: approve|decline|ask, reasoning, confidence,
              source: judge|trust|precedent, matched_precedent? }
Permit      { allow: bool, reason? }
```

## Key Decisions

- **D1 — Runtime accumulation, not pre-flight dry-run.** Layer 2 observes the real execution and
  pauses at the first gate, rather than simulating the workflow first. A dry-run would need every
  tool to honour a no-write mode and still could not know operations that depend on earlier results.
  The cost is accepted: the list shown is "what has run plus what is now attempted", not a complete
  forecast. FR-11 mitigates it by always including what already executed.
- **D2 — The PreToolUse hook is the enforcement point.** It is the only mechanism that can actually
  deny under `bypassPermissions`, and being `async` it can await a verdict, which makes a genuine
  pause possible. The advisory prose channel of 010 becomes a way for the agent to *ask early*, not
  the thing that stops it.
- **D3 — Score derives from tier, it does not replace it.** The declared tier stays the coarse
  invariant layer 1 owns; the 1–5 score is layer 2's currency. This preserves 009/010 and their
  tests, and satisfies FR-36's independent evolution.
- **D4 — The LLM judges; deterministic code grants.** The judge's flexibility is wanted for novel
  cases, but consent must not hinge on a sampled token. FR-17's post-filter is the seam: the model
  can always argue for less friction, and only code can deliver it.
- **D5 — Precedent is exact-fingerprint, not embedding similarity.** A precedent must be explainable
  to the operator ("you approved this same shape 4 times"). Fuzzy matching would make consent
  unauditable, and there is no vector store (P1/P10).
- **D6 — Experience is global; the vault stays knowledge-only.** Trust follows the operator across
  workspaces, and the workspace `vault/` is for knowledge, not operator preferences. JSONL rather than
  CSV because an operation list is nested; still plain text and diffable.
- **D7 — Weights are suggested, never auto-applied.** Adapted from the reference pattern in
  `transcribe-voice-memo`, whose `analyze()` computes `suggested_safe` / `suggested_warn` and leaves
  application to a human. Self-tuning thresholds would let the system quietly widen its own consent.
- **D8 — Decline never generalises.** An operator decline is final for the run (FR-27) and is
  recorded, but only ever narrows future automation (FR-19). The system may learn to stop asking; it
  may not learn to start refusing.

## Constitution impact — APPLIED 2026-08-29 (constitution now 2.0.0)

This feature required a **MAJOR** bump to **2.0.0**, which has been applied: P8 rewritten for bounded
delegation and P12 extended to scoring modifiers. The record of what changed and why follows. P8 currently states that standing consent is
*operator-only* and that the agent "may request **clarification** but can **never** grant or bypass
its own approval" (`memory/constitution.md:111`). FR-15/FR-16 introduce a **non-human checker that
can grant consent**, which is a redefinition of human-in-the-loop, not an extension of it.

Proposed amendment to **P8**, to be applied before implementation:

> Human control over consequential work is satisfied by **per-action review**, by the operator's
> **explicit revocable standing consent**, or by a **bounded checker** acting under that consent. A
> bounded checker MAY answer an approval on the operator's behalf **only** within limits the operator
> sets and code enforces: it may never widen its own authority, may never grant consent for a shape
> without either standing consent or recorded precedent, MUST fail closed to asking, and MUST NOT be
> able to execute. A checker may learn to **ask less**; it may never learn to **refuse more**. Every
> action so approved remains auditable and revertible, and records which party decided.

**P12** additionally extends: rules-as-data now covers the **scoring modifiers** of FR-8/FR-9, not
only the effect table.

## Amendments to existing specs — APPLIED 2026-08-29

- **[[09-planning]] §4.2** currently: *"It never **grants**: the outcome comes from the human or from
  the operator's standing consent (010 FR-2)."* **Amended to:** the outcome comes from the human, from
  standing consent, or from the bounded checker of 011 FR-17, whose grant is filtered deterministically.
- **[[10-risk-engine]] §2** currently declares `action # commit-main | feature-branch |
  require-approval | reject` (`specs/10-risk-engine.md:45`). **Amended to:** add a scoring-modifier
  rule form (name, condition, weight, reason) per 011 FR-8/FR-9, and note that `require-approval` is
  now resolved by the checker rather than terminal. Add as a new §3.2, leaving §3.1's tier table
  intact per D3.
- **[[12-assistant]] AC5** currently: *"The Planning and Risk engines gate all consequential
  executions."* (`specs/12-assistant.md:64`). **Amended to:** name the three layers and the concierge,
  since a two-engine gate no longer describes the architecture. This file has not been touched since
  2026-08-16 and is the stalest of the set.
- **[[13-api]] AC2** currently: *"API calls for consequential work return a plan for approval rather
  than executing immediately."* (`specs/13-api.md:129`). **Amended to:** admit the third outcome —
  a call may execute, return an ask, or be auto-approved on precedent — and record that all surfaces
  now enter via the concierge (FR-23).
- **[[14-chat]] §3.1** holds an ASCII turn-flow tree hard-coding the three tiers and the trust on/off
  branch. **Amended to:** redraw for concierge → execution → report → judge.
- **[[009-approval-optimization]] FR-3** — gating on a resolved action from the message is
  **superseded** by 011 FR-2/FR-6: gating moves to announced operations. 009's effect table (FR-1)
  and reversibility rule (FR-6) survive unchanged.
- **[[010-agent-approval-channel]] FR-2** — "the capability layer decides" is **superseded** by the
  judge plus the FR-17 filter. 010's *ask structurally* half stands; its *grant deterministically*
  half is preserved by FR-17 rather than abandoned.
- **[[008-agent-user-interaction]] FR-18** — unchanged in substance, but the approval card is now
  raised by the concierge on the judge's verdict rather than by the capability layer.

## Downstream specs to reconcile

- [[11-git-workflow]] — the risky→`feature/{name}` branch rule (P12) is still unimplemented; the run
  record now gives it the per-run identity it needs.
- [[17-observability]] — the workflow run record is the natural unit of tracing.
- [[18-security]] — bounded delegation is a security-relevant change and should state the blast
  radius of a compromised judge (answer: it can only ask more, per FR-17/FR-19).
- [[20-testing]] — needs the three-layers-in-isolation testing rule of FR-35.

## Acceptance Criteria

- [ ] **AC-1:** Layer 1 executes correctly with layers 2 and 3 absent, using the default allow-all
  permit and default ask-checker. (FR-3, FR-13, FR-35)
- [ ] **AC-2:** No layer imports another's internals; a static check confirms layer 1 does not import
  layers 2 or 3, and layer 2 does not import layer 3. (FR-34)
- [ ] **AC-3:** A `Write` to `vault/wiki/` by the agent's native tool is announced, scored and
  recorded on the run — proving the gate is no longer message-derived. (FR-4, FR-6, FR-7)
- [ ] **AC-4:** An operation reaching the threshold **pauses** execution; nothing after it runs until
  a verdict arrives, and denial is enforced by the hook rather than by prose. (FR-4, FR-12)
- [ ] **AC-5:** The card presented to the operator lists the gating operation **and** the already-
  executed operations, each with a 1–5 score and a one-line justification. (FR-10, FR-11, FR-25)
- [ ] **AC-6:** Scores derive from tier + data-declared modifiers, clamped 1–5; adding a modifier
  requires no change to the effect table, and adding a capability requires no change to modifiers.
  (FR-8, FR-36)
- [ ] **AC-7:** No modifier references trust mode, precedent or request wording. (FR-9)
- [ ] **AC-8:** A judge `approve` with neither standing consent nor matching precedent is downgraded
  to `ask` by deterministic code. (FR-17)
- [ ] **AC-9:** With an empty experience store every gated operation asks, regardless of judge
  output. (FR-20)
- [ ] **AC-10:** An unavailable or malformed judge response resolves to `ask`. (FR-21)
- [ ] **AC-11:** The judge cannot execute: it has no capability or tool access, and writes only the
  experience store. (FR-22)
- [ ] **AC-12:** After a repeated approval reaches the minimum sample count, the same shape completes
  without a card, and the reply says it was auto-approved on precedent. (FR-17, FR-29)
- [ ] **AC-13:** A judge `decline` is only possible on recorded operator-decline precedent; otherwise
  it asks. (FR-19)
- [ ] **AC-14:** An operator decline stops the operation, ends the run, and is not re-asked in that
  run. (FR-27)
- [ ] **AC-15:** Approval resumes execution synchronously and the paused operation completes in the
  same turn. (FR-26)
- [ ] **AC-16:** Every decision appends exactly one experience record with its `source`, written
  asynchronously; a failure to write does not fail the response. (FR-30)
- [ ] **AC-17:** Both REST and chat reach execution only via the concierge, and behave identically
  for the same request (P9 parity). (FR-23)
- [ ] **AC-18:** Weights are read fresh from the JSON file; the analysis routine suggests changes and
  never writes them back. (FR-32)
- [ ] **AC-19:** The run record is reconstructable after the fact: each operation, its modifiers, the
  verdict, the judge's reasoning, who decided, and the commit. (FR-14, FR-16)
- [ ] **AC-20:** `vault/raw/` remains refused irrespective of score, verdict or trust mode. (P2)

## Implementation note (follow-up, not this document)

New modules, one per layer, so the FR-34 boundary is structural rather than conventional:
`app/execution_gate.py` (the FR-3 contract + default allow-all), `app/workflow.py` (layer 2: run,
`Operation`, scoring, the FR-13 contract + default ask-checker), `app/judge.py` (layer 3: the LLM
risk agent, the FR-17 deterministic filter), `app/experience.py` (JSONL store, fingerprints,
precedent lookup, the suggest-only analysis), `app/concierge.py` (the single entry point).

Changes to existing files: `app/agent.py` — wire the PreToolUse hook to the gate (D2) and demote
`request_approval` to an early-ask; `app/capabilities.py` — remove `_resolve_action` /
`_ACTION_RESOLVERS` message matching and the inline gate from `ask_stream`, announce operations
instead; `app/api.py` and `app/ui.py` — route through the concierge; `app/models.py` — the
`Operation` / `RiskReport` / `Verdict` / `Permit` contracts; `app/config.py` — experience and weights
paths, thresholds, precedent-free ceiling, minimum sample count.

`memory/constitution.md` is at **2.0.0** and the specs listed above carry their amendments, so the
governance gate is cleared and code may now land. Land tests mapping to AC-1…AC-20 in the same change, and keep the existing
`tests/test_approval_optimization.py` and `tests/test_agent_approval_channel.py` green except where
009 FR-3 and 010 FR-2 are deliberately superseded — those assertions must be rewritten, not deleted.
