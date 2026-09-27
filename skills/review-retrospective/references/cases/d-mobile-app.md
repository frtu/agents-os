---
case: D
team: Mobile App Team (illustrative)
format: WRAP — Wishes / Risks / Appreciations / Puzzles, with votes and comment threads
pattern: Future-facing board with almost no past-cycle evidence; misfiled stickies; appreciations naming individuals; a puzzle that is really a decision request
sub-areas: [iOS, Android, Release engineering]
retros: [2026-05-08]
source: "synthetic — generified from a public WRAP retrospective example; not a real team"
---

# Case D — Mobile App Team (illustrative)

> Synthetic example of a **WRAP** retro. WRAP is mostly forward-looking, so the report has little "what happened" evidence — the job is to recover it, and to turn Wishes and Puzzles into owned actions or decisions.

## Team context

- **Sub-areas:** iOS, Android, Release engineering (build pipeline, store submission, feature flags). Weekly release train.
- **Group "Needs improvement" by:** Release pipeline · Code health · Feedback loop.
- **Recurring themes:** deploy speed and reliability; tech debt with no slot; late customer feedback on features.
- **Key metrics to ask for:** release lead time (merge → store), failed/rolled-back releases per month, crash-free sessions, time from feature ship to first user feedback, share of capacity on tech debt.

## Format mapping used

| WRAP column | Template section | Note |
|---|---|---|
| **Wishes** | Start (S/S/C) → candidate actions | A wish implies a current pain; recover it for Needs improvement |
| **Risks** | Needs improvement *or* Risks to watch | Already hurting → Needs improvement; not yet → Risks to watch |
| **Appreciations** | What went well | Keep people's names in appreciations; blameless applies to problems, not thanks |
| **Puzzles** | Open questions → a decision owner + date | A puzzle that asks "when will we…" is a decision request |
| Votes / comment counts | Priority | Highest-voted items must be addressed or explicitly parked |

---

## Retro 2026-05-08

### Raw input (as captured; votes in brackets, comments noted)

**Wishes**
- Faster deployments (2 votes, 3 comments)
- Reliable deployments
- Experiment with introducing a typed language to the codebase (1)
- Everybody showed up on time for standup — don't lose time in the mornings

**Risks**
- Tech debt is building up (1)
- Late feedback on the new features — we got lucky customers loved them

**Appreciations**
- Marketing team — love the new campaign
- Great design work this sprint by *[Designer]*
- Product owner spent lots of time with us this sprint — really appreciated
- *(filed under Appreciations but a question)* "Where did *[Designer]* get those design skills from?"

**Puzzles**
- When are we going to start addressing tech debt? (1)

### Review findings

1. **No evidence of what happened** — every column is feeling or future. Ask for the cycle's numbers before writing a summary: release lead time, rollbacks, crash-free rate. Without them the headline is `[need input]`.
2. **Top-voted wish hides the pain** — "faster deployments" (2 votes, 3 comments) implies deployments are slow. Read the comment thread; recover *how slow* and *why* (build time? store review? manual steps?) and place it in Needs improvement with symptom → impact → cause.
3. **"Faster" and "reliable" are one theme** — release pipeline. One action (investigate the slowest/flakiest step), not two.
4. **Misfiled sticky** — "everybody showed up on time" is an appreciation posted as a wish. Move it to What went well; it isn't an action.
5. **Tech debt appears three times** — risk (1 vote), puzzle (1 vote), and implicitly behind "reliable deployments". Combined, it's the second-strongest theme. The puzzle is a **decision request**: who decides the tech-debt budget, by when?
6. **"We got lucky" is a near-miss** — late feedback that turned out fine is exactly the risk to fix before it doesn't. Treat as Needs improvement (cause: no beta/feedback channel before full rollout?), not luck.
7. **Appreciations naming people — keep them.** Blameless is for problems. Thanks can and should name people. The joke sticky can stay in the appendix; it adds nothing to the report.
8. **Experiment wish needs a box** — "introduce a typed language" is a good experiment; give it a scope (one module), a time-box, and a success test, or park it.

### Proposed report skeleton

**Summary** — `[need input: release lead time / rollbacks this cycle]`. Headline candidate: *"Features landed well with customers, but the team is shipping on a slow, fragile pipeline and a growing tech-debt pile it has no slot for."*

**What went well** — customers responded well to new features (`[need input]`: rating/usage); strong design work by *[Designer]*; product owner closely engaged; standup punctuality; marketing campaign (cross-team).

**Needs improvement**
- **Release pipeline** — deployments slow and unreliable → `[need input]`: lead time, rollbacks → cause `[need input]` (see comment thread).
- **Code health** — tech debt building with no capacity slot → reliability risk → cause: no agreed budget.
- **Feedback loop** — feedback arrives after full rollout → a bad feature would reach everyone → cause suspected: no beta cohort.

**Action items**

| # | Action item | Theme | Owner | Priority | Due | Success signal |
|---|---|---|---|---|---|---|
| 1 | Profile the release pipeline; fix or remove the slowest step | Release pipeline | `[need input]` | High | 2026-05-22 | Merge → store lead time −`[need input]`% |
| 2 | Decide a tech-debt capacity budget (answer the puzzle) | Code health | `[need input]` (EM + PO) | High | next planning | Budget written; used in next sprint |
| 3 | Ship next feature to a beta cohort first; collect feedback before full rollout | Feedback loop | `[need input]` | Med | next feature | Feedback received before 100% rollout |
| 4 | Time-boxed typed-language spike on one module | Experiment | `[need input]` | Low | 2026-06-05 | Go/no-go written up |

### Carry-over for next retro

Check: pipeline lead time (#1) · tech-debt budget decided and used (#2) · beta cohort feedback timing (#3) · spike outcome (#4).
