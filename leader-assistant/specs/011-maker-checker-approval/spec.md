# Feature Specification: Maker–Checker Approval (three independent layers: execute, report, judge)

**Feature ID:** `011-maker-checker-approval`
**Status:** Implemented — governance amendments applied; three layers, concierge and experience store
landed, AC-1…AC-20 and AC-22…AC-24 covered by tests (see *Deviations recorded during implementation*)
**Created:** 2026-08-29 · **Last Updated:** 2026-09-01

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
> (rules-as-data extended to scoring modifiers), and supersedes 009 **FR-3**, 009 **FR-7** and
> 010 **FR-2**.

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
- **FR-39: A shell command MUST be declared by its own effect, not by one tier for all shell use.**
  Layer 1 MUST classify the command it is about to announce against a **data-declared allowlist of
  read-only programs**. When every segment of the command invokes an allowlisted program **and** the
  command contains no file-truncating or appending redirect, no `tee`, no in-place editor and no
  externally-visible token, it MUST be announced as tier `auto` with reversibility "read-only —
  nothing to undo". Any command not **positively** recognised as read-only MUST keep the pessimistic
  `reversible` declaration and its "effects outside the repo are not undone" reversibility.
  Recognition MUST follow **delegation**: where an allowlisted program hands the work to another
  program — a wrapper such as `xargs` or `timeout`, or `find -exec`/`-execdir` — the delegated
  program MUST itself be allowlisted for that segment to count as read-only, and a privilege-raising
  wrapper (`sudo`) MUST never qualify regardless of its payload.
  *Why (delegation):* `find … -exec wc -c {} \;` and `find … | xargs wc -l` are ordinary inventory
  reads, but reading only the leading program mis-declares them — `-exec` can equally run `rm`. The
  answer is to judge the **payload**, not to blanket-refuse the flag: refusing it made a routine size
  listing score 4/5 and gate, while accepting it blindly would let `-exec rm` through. `sudo` is
  excluded because it is the one wrapper whose risk is not its payload's effect.
  *Why:* one blanket declaration for `Bash` put the phrase "not undone" on every shell call, which
  trips the FR-8 `IRREVERSIBLE_OUTSIDE_GIT` modifier unconditionally and gives *reading* a score
  floor of 3 — so `find`/`tail` over the vault scored higher than the same read via `Grep` (tier
  `auto`), and an ordinary inventory reached the gate. The list is **positive** so an unrecognised
  program is treated as mutating: this is recognition of known-safe programs, not static analysis of
  shell (Non-Goals), and it fails closed. Destructive commands are unaffected — they are not on the
  allowlist and `DESTRUCTIVE_SHELL` still lifts them to a gating score.

- **FR-42: A shell command confined to the workspace MUST be declared as git-covered, not as
  possibly escaping it.** When every path-like token in the command resolves inside the workspace
  root, layer 1 MUST announce the same reversibility it gives an equivalent `Write`/`Edit` — the
  turn's commit is the undo. The pessimistic "effects outside the repo are not undone" wording MUST
  be reserved for commands with a token that resolves outside, or none that can be resolved at all.
  *Why:* the blanket `Bash` reversibility is a disjunction — "`git revert` covers workspace files;
  effects outside the repo are not undone" — and FR-8's `IRREVERSIBLE_OUTSIDE_GIT` matches on that
  text, so it fired on every shell write regardless of where the write landed. `mkdir -p` of seven
  `vault/wiki/` scaffold directories therefore scored 4 and gated, while the identical effect through
  `Write` scored 2 and ran: the same blast radius priced differently because of which tool spelled
  it. Correcting the declaration also removes the *need* to consult layer 3 for routine ingest
  writes, which matters because FR-17's filter fails closed to `ask` **before** trust mode is
  consulted — so a transient judge outage strands work that standing consent should have covered.
  Safety is unchanged: an escaping token keeps the pessimistic declaration, and `DESTRUCTIVE_SHELL`
  and `EXTERNALLY_VISIBLE` still lift `rm -rf`, `sed -i` and `curl` to a gating score on their own.

- **FR-45: A heredoc body is data, not command syntax, and MUST NOT be classified.** Before any
  effect classification — read-only recognition (FR-39), path confinement (FR-42), external-token
  detection (FR-5 `external`), destructive-token matching (FR-8) or effect-class fingerprinting
  (FR-41) — layer 1 MUST strip every here-document body from the command, leaving the redirect
  operator and delimiter. The body's *content* MUST NOT contribute to any score.
  *Why:* the payload of `cat > page.md <<'EOF' … EOF` is the **page being written**, and it was
  scanned as though it were shell. A source précis whose prose merely contained the word `curl`
  set `external=True`, which in turn skipped FR-42's confinement branch and restored the
  "not undone" wording — so a wiki page scored **5/5, above the FR-18 ceiling, because of a word in
  its own text**. Measured: the identical write scored 4 with the body `body` and 5 with the body
  `use curl to fetch, then rm the tmp`. Content-dependent scoring is not a description of an
  operation's effect, so it also violates FR-9/P12. Safety is unchanged: the redirect target and
  every program outside the body are still classified exactly as before.

- **FR-46: Command splitting MUST be quote-aware.** When layer 1 splits a command into segments to
  classify it, separators (`|`, `||`, `&&`, `;`, `&`) appearing inside single or double quotes MUST
  NOT split it. *Why:* the splitter was a plain regex, so `grep -n "record\|precedent\|awaiting" f`
  shattered into phantom segments — `precedent\`, `awaiting" f` — whose leading words are not
  allowlisted programs. Under FR-39's deliberately pessimistic "unknown program means assume it
  mutates", a **pure read** was therefore declared `reversible`, and with the FR-42 wording it
  reached a gating score. Confirmed live: a read-only `grep` of one source file scored 5/5, and the
  judge's own reasoning recorded the modifiers as "misclassifications of a read". Any grep
  alternation, and any quoted `;`/`&`/`|`, is affected — which is most non-trivial inspection.

- **FR-47: A flag's argument MUST NOT be mistaken for a subcommand.** When resolving a
  conditionally-read-only program's subcommand (FR-39's `git` case), layer 1 MUST skip both the
  flags and the **arguments those flags consume** (`git -C <path>`, `git -c <k>=<v>`,
  `--git-dir <path>`). *Why:* the resolver took the first non-`-` token, so in
  `git -C . status --porcelain` the subcommand read as `.` rather than `status`. `.` is not on the
  read-only subcommand list, so the canonical way to inspect a workspace repo from outside it was
  declared a mutation. This is the defect that gated the **first** operation of the 2026-09-02
  ingest session — a read-only `git status` — and it silently degrades FR-41 fingerprints too,
  since `effectful_programs` then reports `git` for a read, so repeated approvals of the same
  intent never accumulate into FR-17 precedent.

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
- **FR-40: Blast-radius modifiers MUST NOT fire on an `auto`-tier operation.** The modifiers that
  describe the *extent* of a change — breadth of targets and target sensitivity — MUST be conditioned
  on the operation changing something. Reading many files is not breadth of change, and reading
  sensitive state is not corrupting it. *Why:* both conditions match the target **text**, so
  `tail vault/wiki/log.md` scored as if it were rewriting the ledger and an inventory naming three
  paths scored as a sweep — together enough to push a pure read to 5 and past the FR-18
  precedent-free ceiling, where no trust mode can clear it. This mirrors the guard
  `PRIVILEGE_GRANTING` already carries, and remains FR-9-compliant: the condition reads the declared
  tier of the operation in front of it and nothing else.
- **FR-43: The knowledge store is a safe-by-design write target — breadth MUST NOT gate it.** When
  every path-like target of a state-changing operation resolves inside the workspace's `vault/wiki/`
  or `vault/output/` tree — and none of them is a sensitive control file (the FR-9 `SENSITIVE_TARGET`
  set) — `BREADTH_MANY_TARGETS` MUST NOT fire, however many pages the operation touches. *Why:*
  `vault/wiki/` is the LLM's own durable knowledge store and `vault/output/` its generated artifacts
  (P1); writing to them in bulk is the sanctioned ingestion workflow, not the anomalous sweep breadth
  exists to surface, and the whole blast radius is one `git revert` of the turn's commit (FR-42).
  Breadth was only ever a proxy for "a change the operator wants to see before it lands"; a batch of
  additive, git-covered pages in the very store the assistant exists to fill is not that — so an
  ingest of seventeen sources must not gate on its own page count. Safety is unchanged elsewhere: a
  target that escapes the store, a destructive verb (`DESTRUCTIVE_SHELL`), an external effect
  (`EXTERNALLY_VISIBLE`), or a sensitive control file (`SENSITIVE_TARGET`, e.g. `vault/wiki/log.md`)
  each still fires on its own, and breadth still fires for a sweep anywhere outside the store. This
  refines FR-40's guard, which reads the same declared tier and nothing else, so it stays FR-9
  compliant.
- **FR-48: A redirect MUST be scored by where it lands, not by its syntax.** A file-creating or
  truncating redirect MUST NOT count as a destructive token on its own. It MUST raise the score only
  when the write is **not** covered by a git revert — i.e. when layer 1 declared the command as
  escaping the repo (FR-42). *Why:* `DESTRUCTIVE_SHELL` matched a bare `>` at weight 2, which on the
  `reversible` base of 2 put **every** heredoc write at exactly the gate threshold. Measured:
  `cat > vault/wiki/sources/notes/X.md <<EOF` scored 4 — *identical to*
  `rm -rf vault/wiki/concepts`, also 4 — while the same effect through `Write` scored 2 and ran. So
  routine ingest could never score below the gate however small the batch, and the parity gap
  between two doors to one mutation is a P9 violation. `>` describes transport, not effect, so
  scoring it also violated FR-9/P12. Safety is preserved and sharpened: a redirect that escapes the
  repo now scores 5 (base 2 + `IRREVERSIBLE_OUTSIDE_GIT` + `REDIRECT_ESCAPES_REPO`) where it
  previously scored 3, and `rm`, `sed -i`, `truncate` and `git reset --hard` are untouched.

- **FR-49: A paused run MUST still permit reads and the approval-request channel.** While a run is
  `awaiting` a verdict, layer 2 MUST continue to permit `auto`-tier operations and MUST always
  permit the capability by which approval is requested. Everything else stays refused (FR-12).
  *Why:* the pause refused **every** announcement, including reads and `request_approval` itself, so
  Constitution P8 v2.0.0's "MUST fail closed to asking" was unsatisfiable — the channel needed to
  ask was shut by the same pause. FR-15's three outcomes (ask / auto-approve / decline) collapsed to
  an undocumented fourth: hang. Observed four times in one session, twice on a pure read. An
  `auto`-tier operation changes nothing by definition (FR-40 already relies on this), so permitting
  it cannot widen the blast radius the operator is being asked about; refusing it only stops the
  assistant from explaining what it is asking for.

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
  `ask`, **except** where the bounded passthrough of FR-44 applies.
- **FR-44: A dead checker MUST NOT deadlock low-risk, recoverable work.** When FR-21's condition
  holds — the judge is unavailable, timed out, or malformed, so no recommendation is produced — the
  deterministic filter MUST auto-approve the gating operation **iff** it is **reversible-tier**
  (git-recoverable; tier ≠ `approval`) **and** its score is at or below a data-declared
  `judge_unavailable_safe_ceiling` (default = `gate`). Every other case — an `approval`-tier
  executable action (`import_skill`, `create_workspace`), or any operation scoring above the ceiling
  — MUST still resolve to `ask`. A passthrough MUST record source `filter` and MUST NOT establish
  precedent (only operator decisions do, FR-30), so it is auditable and revertible but never
  bootstraps its own authority. *Why:* FR-21 and FR-12 together let one flaky checker call brick a
  whole turn, stranding even the trivially-reversible work a healthy judge would have waved through;
  a reversible mutation is git-committed and revertible (FR-6), so running it under a dead checker
  costs at most one `git revert`, while an executable approval-tier action — the reason the gate
  exists — still waits for a human. The ceiling is rules-as-data (P12): setting it below `gate`
  restores pure fail-closed. This is the deterministic filter's own rule (FR-17): the model cannot
  reach it, because there is no model response when it fires.
- **FR-22:** The judge MUST have **no execution capability** — no capability-layer access, no tools,
  no filesystem writes other than the experience store.

### Concierge / orchestrator

- **FR-23:** Every user→backend call MUST enter through the concierge, on **both** REST and chat
  (P9). No surface may reach execution directly.
- **FR-24:** The concierge owns the sequence and nothing else: open run → invoke execution → on pause
  consult the judge → surface an ask if required → resume on answer → record experience
  asynchronously.
- **FR-25:** An ask MUST surface as the existing **008 approval interaction card**. This feature adds
  no new asking surface and no new REST route for asking. The card's **prompt MUST stay a concise,
  scannable one-liner**: the gating operation's target is **summarized** (first line, truncated) so the
  choices remain visible, never displaced by a raw payload. A shell command is the motivating case — a
  multi-line / heredoc `Bash` target would otherwise fill the prompt and push the options off-screen.
  The **full, untruncated** target MUST still be preserved in the persisted record (the durable risk
  assessment) so nothing an operator needs to audit is lost.
- **FR-26:** On operator approval, execution MUST **resume synchronously** and complete the paused
  operation within the same request/turn.
- **FR-27:** An operator decline MUST be **final** for that operation and run: it does not execute,
  the run terminates, and the same operation MUST NOT be re-asked within the run.
- **FR-38:** When a run pauses, the operator MAY approve **every operation of the same shape** for the
  remainder of that run, not only the paused one. *Shape* is `kind:name` — the capability or tool
  identity, **target-independent** — so approving one skill import authorises the rest of a bulk
  install (`import_skill` on any name) without a card per skill. The approval card carries a second,
  optional affirmative option alongside "approve this one"; picking it seeds a **standing within-run
  shape grant** that is honoured across the synchronous FR-26 resume re-run, so a bulk of similar
  operations completes with **one** decision instead of one card per target. The grant is scoped to
  the single authorised run (a new user request is a new run with no grants) and is **affirmative
  only**: FR-27 and D8 are unchanged — a decline never generalises to a shape, and a specific
  operation the operator has declined stays declined even under a shape grant. This is how "ask for
  all at once" is realised under D1: layer 2 cannot forecast the run, so batch consent is granted
  forward over the shape rather than by pre-flight look-ahead.

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
- **FR-41: A shell fingerprint MUST identify the command's effect class, not its exact program
  sequence.** Matching stays **exact string equality on the canonical form** — no embeddings, no
  similarity score, no vector store (D5, P1/P10). The tolerance for variation comes from normalising
  more aggressively, so that slight variations of one intent canonicalise to the *same* string:
  1. a command classified read-only under FR-39 fingerprints as `read-only`, regardless of which
     read programs it used or in what order;
  2. otherwise the class is the **set** of effect-bearing programs — allowlisted read-only helpers
     removed — deduplicated, **sorted**, and capped at three (e.g. `git+rm`);
  3. if no effect-bearing program survives that filter the class is `write`, which is the case for a
     command built only from read programs plus a redirect.
  Argument values, program order, and read-only helpers are therefore not part of the identity:
  `ls -la && rm -rf x` and `rm x; ls` are one shape. *Why:* the previous rule keyed on the ordered
  first three program names, so every phrasing of an inventory was a brand-new shape at zero
  approvals. With FR-17 requiring three approvals of one fingerprint, precedent for ordinary shell
  work could never accumulate and the operator was asked forever. Coarsening is deliberately
  **one-way** and applies only to `Bash`; path-target fingerprints are unchanged. Records written
  under the previous rule simply stop matching and precedent re-accumulates — acceptable because the
  store is append-only and every fingerprint in it stays readable.
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
- **FR-37:** An operation MAY carry a **declared risk level** describing the danger of the thing it
  installs or runs, distinct from the mechanical reversibility of the act itself — the first use is
  skill import, where the level is the skill's own `risk-level` ([[005-skill-import]] FR-12/FR-13).
  When present, the level is the **authoritative** score for that operation: layer 2 MUST map it
  through a **data-declared** table (`.leader-risk-weights.json` → `skill_risk_level`, default
  `low`=2 / `medium`=3 / `high`=4 / `critical`=5, clamped 1–5) **instead of** the tier base and the
  generic effect modifiers of FR-8. This keeps a trivially-reversible-but-dangerous install (a
  symlink that grants runnable behaviour) from being pinned at the ceiling by the reversibility
  modifiers, and keeps a genuinely dangerous one above the gate. The mapping is rules-as-data (P12)
  and still describes only the operation's own effect (FR-9): it references no trust mode, precedent
  or request wording. An operation with no declared level scores by FR-8 exactly as before.

## Judge-unavailable deadlock escape — RATIFIED as FR-44 (2026-09-02)

> **Status: approved and implemented.** The operator reviewed the pending proposal below and chose
> the narrow, deterministic option: a bounded passthrough in the filter, not a circuit-breaker card.
> The behaviour is now **FR-44** in the Functional Requirements above; this section keeps the defect
> record and the reasoning behind the shape that was chosen.

**The defect (observed 2026-09-02, session `e9858c0a3561`).** FR-21 (fail closed on an unavailable,
timed-out, or malformed judge) is correct, and FR-12 (pause the whole run at the first gating
operation) is correct — but *together* they can brick a turn with no operator escape hatch. In the
observed run the judge returned one malformed response; FR-21 correctly resolved it to `ask`, FR-12
paused the run, and every subsequent tool call — including read-only ones and even a fresh
`request_approval` — was refused with "run paused awaiting a decision." Approving the card did not
help, because the *next* operation hit the same failing judge and re-paused. The only recovery was
to abandon the session. A single flaky checker call therefore denies all progress, including the
read-only work that never needed the judge, and the operator has no in-turn way out.

**Why it was not already covered.** FR-21 decides one operation's verdict; it said nothing about a
*persistently* down checker. FR-12's global pause is a safety property (nothing runs past an
unresolved gate) but had no escape. Trust mode does not help: FR-21 fails closed regardless of
standing consent, by design.

**What was chosen (FR-44).** An extra branch in the deterministic filter, taken only when the judge
produced no recommendation: a **reversible-tier** operation at or below `judge_unavailable_safe_ceiling`
auto-runs; everything else still asks. It is deliberately the *narrowest* of the options considered,
and it lives in the filter (FR-17) rather than the concierge because the decision is data-only —
tier and score, both already on the report — and the model cannot influence a branch that only fires
when the model is silent. The safety line is the tier: a git-recoverable mutation under a dead
checker costs at most one `git revert` (FR-6), whereas an `approval`-tier executable action — the
reason the gate exists — still waits for a human. Because everything reaching the filter already
scored ≥ `gate`, the default ceiling of `gate` means the passthrough fires only for the score-at-the-
floor operations and still stops the score-above-floor ones.

**Alternatives considered and declined.** (1) A **checker circuit-breaker card** after *N* fail-closed
verdicts — richer, but it adds a new interaction kind and a new concierge state for a degraded mode
that FR-44 already makes rare; deferred, not rejected. (2) Letting **`auto`-tier reads** bypass a
dead judge — unnecessary once reads are declared `auto` (FR-39), because an `auto` operation never
reaches the gate and so never reaches the judge at all; the scoring fixes of FR-39/FR-43 removed the
misclassification that made this session's reads gate in the first place.

## Data & file contracts

```text
<workspace root>/.leader-experience.jsonl   append-only decision records (FR-28/FR-29)
<workspace root>/.leader-risk-weights.json  modifier weights, bands, thresholds (FR-28/FR-32)
<workspace>/vault/wiki/log.md               executed mutations, as today (P8)
```

```text
Operation   { op_id, kind: capability|tool, name, target, tier, reversibility,
              external, declared_risk?, score 1-5, modifiers[], justification, status }
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
- **D9 — Batch consent is shape-scoped and run-scoped.** "Approve all similar in this request"
  (FR-38) grants forward over the operation *shape* (`kind:name`, ignoring target) for the one
  authorised run, because the dynamic agent reveals operations one at a time and D1 rules out
  look-ahead. It is deliberately **not** a standing precedent: it dies with the run and is never
  written to the experience store, so it cannot quietly widen the checker's authority (P8). Only
  approvals learn (FR-17); a batch grant is a one-request convenience, not a taught trust.
- **D10 — Reading is not an effect; the fix belongs in the declaration, not the thresholds.** Routine
  work gated because a read was *declared* like a write (FR-39) and then scored for extent it did not
  have (FR-40) — so the correction is to describe the effect accurately, not to raise `gate` or blunt
  the modifier weights. Raising `gate` to 5 would be the tempting one-line fix and is wrong: the
  `approval` tier bases at 4 and `skill_risk_level.high` maps to 4, so it would silently auto-run
  every approval-tier action and every high-risk skill install. Zeroing `BREADTH_MANY_TARGETS` and
  `SENSITIVE_TARGET` in the weights file would work today but disarms them for *writes*, which is
  the only place they were ever meant to fire. Both remain available to an operator as hand tuning
  (FR-32); neither is the design. *(Refined by D11: `BREADTH_MANY_TARGETS` stays armed for writes
  everywhere except the knowledge store — see FR-43.)*

- **D11 — The knowledge store is exempt from breadth (FR-43).** D10 kept `BREADTH_MANY_TARGETS`
  armed for writes because a sweep across many files is exactly what an operator wants to see before
  it lands. But the one place the assistant writes in bulk *by design* is `vault/wiki/` (its own
  durable knowledge store, P1) and `vault/output/` (its generated artifacts) — an ingest of
  seventeen sources writes seventeen pages because that is the job, not because it is running wide.
  So a state-changing operation whose path targets are *all* inside `vault/wiki/`/`vault/output/`,
  none of them a sensitive control file (the FR-9 `SENSITIVE_TARGET` set — e.g. `vault/wiki/log.md`),
  does not count as broad, however many pages it touches. This is narrower than zeroing the modifier
  (D10's rejected shortcut): breadth still fires for any sweep that escapes the store, and every
  other modifier still fires inside it.

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
- **[[009-approval-optimization]] FR-7** — trust mode as an *unconditional* bypass of every
  approval-tier action is **superseded** by 011 FR-17/FR-18/FR-20. Trust mode remains the operator's
  standing consent and remains the only thing that can grant one (009 FR-11 and 010's operator-only
  rule stand), but it is now consent **bounded by** the precedent-free ceiling and by cold start: it
  authorises a judge `approve` rather than skipping the judge. Consequence worth stating plainly —
  on a fresh install, and for any novel operation scoring above the ceiling, trust mode does **not**
  stop the ask. That is scenario 4, not a regression. 009 FR-8 (persistence) and FR-9 (per-request
  override precedence) survive unchanged: the hint still reaches the judge from the same two places
  with the same precedence.
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

- [x] **AC-1:** Layer 1 executes correctly with layers 2 and 3 absent, using the default allow-all
  permit and default ask-checker. (FR-3, FR-13, FR-35)
- [x] **AC-2:** No layer imports another's internals; a static check confirms layer 1 does not import
  layers 2 or 3, and layer 2 does not import layer 3. (FR-34)
- [x] **AC-3:** A `Write` to `vault/wiki/` by the agent's native tool is announced, scored and
  recorded on the run — proving the gate is no longer message-derived. (FR-4, FR-6, FR-7)
- [x] **AC-4:** An operation reaching the threshold **pauses** execution; nothing after it runs until
  a verdict arrives, and denial is enforced by the hook rather than by prose. (FR-4, FR-12)
- [x] **AC-5:** The card presented to the operator lists the gating operation **and** the already-
  executed operations, each with a 1–5 score and a one-line justification. (FR-10, FR-11, FR-25)
- [x] **AC-6:** Scores derive from tier + data-declared modifiers, clamped 1–5; adding a modifier
  requires no change to the effect table, and adding a capability requires no change to modifiers.
  (FR-8, FR-36)
- [x] **AC-7:** No modifier references trust mode, precedent or request wording. (FR-9)
- [x] **AC-8:** A judge `approve` with neither standing consent nor matching precedent is downgraded
  to `ask` by deterministic code. (FR-17)
- [x] **AC-9:** With an empty experience store every gated operation asks, regardless of judge
  output. (FR-20)
- [x] **AC-10:** An unavailable or malformed judge response resolves to `ask` for an approval-tier or
  above-ceiling operation; the FR-44 passthrough is the only exception. (FR-21, FR-44)
- [x] **AC-11:** The judge cannot execute: it has no capability or tool access, and writes only the
  experience store. (FR-22)
- [x] **AC-12:** After a repeated approval reaches the minimum sample count, the same shape completes
  without a card, and the reply says it was auto-approved on precedent. (FR-17, FR-29)
- [x] **AC-13:** A judge `decline` is only possible on recorded operator-decline precedent; otherwise
  it asks. (FR-19)
- [x] **AC-14:** An operator decline stops the operation, ends the run, and is not re-asked in that
  run. (FR-27)
- [x] **AC-15:** Approval resumes execution synchronously and the paused operation completes in the
  same turn. (FR-26)
- [x] **AC-16:** Every decision appends exactly one experience record with its `source`, written
  asynchronously; a failure to write does not fail the response. (FR-30)
- [x] **AC-17:** Both REST and chat reach execution only via the concierge, and behave identically
  for the same request (P9 parity). (FR-23)
- [x] **AC-18:** Weights are read fresh from the JSON file; the analysis routine suggests changes and
  never writes them back. (FR-32)
- [x] **AC-19:** The run record is reconstructable after the fact: each operation, its modifiers, the
  verdict, the judge's reasoning, who decided, and the commit. (FR-14, FR-16)
- [x] **AC-20:** `vault/raw/` remains refused irrespective of score, verdict or trust mode. (P2)
- [ ] **AC-21:** A run that gates on N operations of the same shape (e.g. N high-risk `import_skill`
  calls) raises **one** card; the operator picking "approve all" lets all N complete in the resumed
  turn, while a plain "approve" completes only the paused one and re-asks the next. (FR-38, D9)
- [x] **AC-22:** A read-only shell inventory of a workspace — `find`/`ls`/`tail`/`echo` over `vault/`,
  including `tail` of `vault/wiki/log.md` — is announced `auto`, scores **1**, and runs with no card;
  the same paths under `rm -rf`, `sed -i` or a truncating redirect still reach the gate. (FR-39,
  FR-40)
- [x] **AC-23:** `BREADTH_MANY_TARGETS` and `SENSITIVE_TARGET` fire on no `auto`-tier operation, and
  still fire on the `reversible` / `approval` equivalents of the same targets. (FR-40, FR-9)
- [x] **AC-24:** Two read-only commands differing in program order, arguments and which read programs
  they use produce **one** fingerprint, so repeated operator approvals accumulate toward FR-17's
  minimum sample count instead of resetting; a mutating command fingerprints on its effect-bearing
  programs alone and never collides with the read-only class. (FR-41, FR-31, FR-17)
- [x] **AC-25:** A read that delegates to an allowlisted program — `find … -exec wc -c {} \;`,
  `find … | xargs wc -l`, `timeout 30 find …` — is announced `auto` and scores **1**, while the same
  shapes delegating to a mutating program (`-exec rm`, `xargs rm`) or raising privilege (`sudo cat`)
  keep the `reversible` declaration and reach the gate. (FR-39)
- [x] **AC-26:** `mkdir -p` of several `vault/wiki/` scaffold directories scores the same as the
  equivalent `Write` and runs without consulting layer 3, while the same command naming a path
  outside the workspace keeps `IRREVERSIBLE_OUTSIDE_GIT`; `rm -rf` and `sed -i` inside the workspace
  still reach the gate on `DESTRUCTIVE_SHELL` alone. (FR-42, FR-8)
- [x] **AC-27:** A `cd <path> && wc -l … && sed -n '1,200p' …` inspection is announced `auto` and
  scores **1**, whether the path is inside or outside the workspace — `cd` writes nothing, so a chain
  of reads behind it carries no `IRREVERSIBLE_OUTSIDE_GIT`/`PRIVILEGE_GRANTING`/`BREADTH`. (FR-39,
  AC-22)
- [x] **AC-28:** A single `Write`/`Edit`, or a bulk write, whose targets are all under `vault/wiki/`
  scores below `gate` no matter how many pages it touches — `BREADTH_MANY_TARGETS` never fires in the
  knowledge store — while the same count of targets under a non-store path (e.g. `docs/`) still fires
  breadth, and a write to `vault/wiki/log.md` still fires `SENSITIVE_TARGET`. (FR-43, D11)
- [x] **AC-29:** With the judge unavailable/timed-out/malformed, a **reversible**-tier gating
  operation scoring at or below `judge_unavailable_safe_ceiling` resolves to `approve` with source
  `filter`, and the record establishes **no** precedent (a later healthy run with the same shape
  still asks). (FR-44, FR-30)
- [x] **AC-30:** With the judge unavailable, an `approval`-tier operation (`import_skill`,
  `create_workspace`) still resolves to `ask`, and so does any reversible operation scoring **above**
  the ceiling; setting `judge_unavailable_safe_ceiling` below `gate` restores pure fail-closed for
  all operations. (FR-44, FR-21)

## Implementation note (follow-up, not this document)

New modules, one per layer, so the FR-34 boundary is structural rather than conventional:
`app/execution_gate.py` (the FR-3 contract + default allow-all), `app/workflow.py` (layer 2: run,
`Operation`, scoring, the FR-13 contract + default ask-checker), `app/judge.py` (layer 3: the LLM
risk agent, the FR-17 deterministic filter), `app/experience.py` (JSONL store, fingerprints,
precedent lookup, the suggest-only analysis), `app/concierge.py` (the single entry point).

Changes to existing files: `app/agent.py` — wire the PreToolUse hook to the gate (D2) and demote
`request_approval` to an early-ask; `app/capabilities.py` — remove the inline gate from `ask_stream`
and announce operations instead; `app/api.py` and `app/ui.py` — route through the concierge;
`app/models.py` — the `Operation` / `RiskReport` / `Verdict` / `Permit` contracts; `app/config.py` —
experience and weights paths, thresholds, precedent-free ceiling, minimum sample count.

`memory/constitution.md` is at **2.0.0** and the specs listed above carry their amendments, so the
governance gate is cleared and code may now land. Land tests mapping to AC-1…AC-20 in the same change, and keep the existing
`tests/test_approval_optimization.py` and `tests/test_agent_approval_channel.py` green except where
009 FR-3, 009 FR-7 and 010 FR-2 are deliberately superseded — those assertions must be rewritten,
not deleted.

### Deviations recorded during implementation

- **`_resolve_action` / `_ACTION_RESOLVERS` are kept**, contrary to the note above. They are demoted
  from *gatekeeper* to *dispatcher*: they answer "which capability does this message invoke", and the
  announced operation they produce is what faces the gate. FR-2 is satisfied because the **decision**
  moved behind `execution_gate.announce()`, not because the dispatch table was deleted. Removing it
  would leave chat with no route to `create_workspace` (deliberately absent from the agent's MCP
  tools) and no gating at all on the offline path.
- **A capability pause is recorded twice**: as the 008 card (FR-25) *and* as the durable
  `pending_plan` 009 already used. `approve=true` and a card click therefore both resolve the same
  paused operation (`concierge._approve_plan` pre-grants exactly the plan's operation key), and either
  survives a restart.
- **`RiskAssessment` gained `workspace` / `interaction_id` / `conversation_id`.** FR-25 forbids a new
  asking surface, which left a REST `409` unanswerable — a refusal with no address. These three fields
  are that address: they name the card raised for the ask and the existing
  `POST /api/chat/interaction` route that answers it. No new route, no new surface. All three are
  needed: cards live in one workspace's `sessions/`, and that is not always the workspace the
  operation targets (a card about *creating* a workspace is hung on the default), so the id pair
  alone resolves to the wrong conversation for any pause outside the default workspace.
- **The judge is stubbed in the test suite**, not disabled (`tests/conftest.py::offline_judge` returns
  a fixed `approve`). Determinism has to come from somewhere, and pinning the *recommendation* leaves
  the FR-17…FR-20 filter as the thing under test; the parse and fail-closed paths keep their unit
  coverage in `tests/test_judge.py`.
- **AC-2's static check inspects the callee, not the source text.** A route legitimately *mentions* a
  capability — it passes one in as the thunk the concierge runs behind the gate — so a text match
  flags every route. `tests/test_maker_checker_integration.py` unparses the callee of each `await` /
  `async for` instead, and the import scan walks function-local imports too, since that is where the
  layers break their cycles.

### FR-39…FR-41 — recorded during implementation (2026-09-01)

- **The shell effect vocabulary lives in `app/execution_gate.py`**, next to `TIERS`. Layer 1 needs it
  to declare a tier (FR-39) and the experience store needs the same answer to fingerprint a command
  (FR-41), and neither may import the other (FR-34). It is *description*, not policy — no score, no
  threshold, no trust mode — so the contract module stays dependency-free and AC-2's check still
  passes.
- **The effect class is computed per command segment, not by filtering program names.** Filtering the
  names against the read-only allowlist collapsed `git push` to the generic `write` class, because
  `git` is on the allowlist as a program. Classifying each segment on how it was actually called
  keeps `git push` → `git` distinct from `echo hi > f` → `write`, which is the difference between an
  auditable precedent and an opaque one.
- **A wrapper's wrapped command is unwrapped** (`xargs`, `sudo`, `timeout`, `sh -c`, …). Without it,
  `find … | xargs rm` named `xargs` as the effect: it fingerprinted as a wrapper call and, since
  `DESTRUCTIVE_SHELL` required whitespace *after* the verb, `rm` in final position matched nothing —
  the deletion scored 3 and ran unprompted. The verb patterns are now anchored `(?=\s|$)`, which
  still excludes the quoted mentions (`grep -rn "rm" .`) the trailing-space rule existed to exclude.
  This was a pre-existing hole in the coarse detector, surfaced by FR-41's segment analysis.
- **Delegation is judged by payload, and only some wrappers may delegate a read.** The first cut
  refused `-exec`/`-execdir` outright as mutating flags, which left `find … -exec wc -c {} \;` — a
  plain size listing — declared `reversible` and scored 4/5, i.e. still gating on the very run FR-39
  was written for. It is now read-only when the delegated program is itself allowlisted. Only
  `nice`/`time`/`timeout`/`xargs` may pass a read through: a shell interpreter (`bash -c '…'`)
  re-parses its quoted argument, so segment splitting cannot see the whole command and a reading
  payload proves nothing, and `sudo`'s risk is the privilege rather than the payload's effect.
- **"Path-like" (FR-42) is read over-inclusively, and confinement must be unanimous.** A sed script
  (`s/a/b/`) is indistinguishable from a relative path at this level, so it is collected as one. That
  is sound only because the check requires *every* token to resolve inside and at least one to
  resolve at all: a spurious token can cost a command its downgrade but never earn it one, and a
  command that names nothing resolvable keeps the pessimistic declaration instead of being excused
  for its silence.
- **A segment whose first token is a flag names no program.** Splitting on `;` cuts
  `find … -exec wc {} \; -delete` into a trailing `-delete` segment, which fingerprinted as
  `tool:Bash:-delete` — a flag recorded where FR-41 requires an effect-bearing program. Leading flags
  are now dropped with leading assignments. Scoring was already correct (`DESTRUCTIVE_SHELL` matches
  the text); the defect was an unauditable entry in the append-only store.

### FR-43 + `cd` read-only fix — recorded during implementation (2026-09-02)

- **`cd`/`pushd`/`popd` are read-only and belong on the allowlist.** A session ingest paused three
  times on read-only inspections shaped `cd <path> && wc -l … && sed -n '1,200p'` — each declared
  `reversible` and scored 5/5 via `IRREVERSIBLE_OUTSIDE_GIT` + `PRIVILEGE_GRANTING` + `BREADTH`, above
  the precedent-free ceiling, so the judge's *approve* could not stand. Root cause: `cd` was absent
  from `READ_ONLY_PROGRAMS`, so its segment failed FR-39's positive test and the whole `&&` chain
  kept the pessimistic `reversible` declaration even though every real segment only read. `cd`,
  `pushd`, and `popd` change the shell's working directory and write nothing; adding them lets a
  `cd X && <reads>` chain be recognised as `auto`. (FR-39)
- **FR-43 makes the knowledge store's write breadth structurally safe, not luckily safe.** A bulk
  `vault/wiki/` write already scored at most 3 today (below `gate` 4) — but only because no *second*
  modifier happened to stack. The operator's guarantee is that ingest approval is independent of file
  count, so `_many_targets` now returns `False` when every path target resolves inside
  `vault/wiki/`/`vault/output/` and none is a `SENSITIVE_TARGET`. Seventeen pages or one, breadth
  never fires in the store; it still fires for any sweep that escapes it. (FR-43, D11)
- **A bare variable-assignment segment is a read-only no-op, not an unrecognised command.** A second
  ingest session stalled the same way on read-only recon written as `R=<vault-path>; find $R … | sed
  … | sort | uniq` — the operator's habit of assigning a long path to a variable first. The leading
  `R=<path>;` segment names no program (assignments are environment, stripped before the program
  scan), and a program-less segment was read as "assume it mutates", dragging the whole `;`/`&&`/`|`
  chain from `auto` to `reversible` so `IRREVERSIBLE_OUTSIDE_GIT` + `BREADTH` scored it 4–5 and gated.
  A pure `VAR=value` segment sets shell state and writes nothing (command substitution in the value
  is already refused by the `_SUBSTITUTION` guard), so it is now recognised as read-only. Any
  program-less segment that is *not* a pure assignment keeps the pessimistic declaration. (FR-39)
