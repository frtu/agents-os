---
case: A
team: Checkout Product Squad (illustrative)
format: Three columns — What went well / What to improve / Action items (sprint retro)
pattern: Thin sticky-note board — actions restate problems ("try to…", "find better ways…"), venting notes, no numbers; Produce mode worked end-to-end
sub-areas: [Web checkout, Mobile checkout, QA automation]
retros: [2026-06-12]
source: "synthetic — generified from public sprint-retrospective board examples; not a real team"
---

# Case A — Checkout Product Squad (illustrative)

> Synthetic example of the most common retro input: a three-column sticky-note board, exported as text. Shows how Produce mode turns thin input into a report without inventing facts.

## Team context

- **Sub-areas:** Web checkout, Mobile checkout, QA automation (end-to-end suite). Two-week sprints; 7 engineers, 1 PM, 1 designer; recently moved to a new front-end stack.
- **Group "Needs improvement" by:** Planning & estimation · Ways of working · Engineering health.
- **Group action-item Theme by:** Planning, Meetings, Quality, Tech debt, Team.
- **Recurring themes to track:** estimation accuracy; meeting load vs focus time; tech debt getting crowded out by features.
- **Key metrics to ask for:** sprint commitment vs completed (points or stories), carry-over stories per sprint, meeting hours / engineer / week, E2E suite pass rate & runtime, escaped defects.

---

## Retro 2026-06-12

### Raw input (board export, as captured)

**What went well**
- Good collaboration
- Willingness to work on new tech stack
- New team member onboarding going well
- Having a mid-sprint meeting to discuss future stories
- Good pairing despite remote work
- E2E automation has really improved things

**What to improve**
- Before picking any story, each story should have clear acceptance criteria
- Less meetings more coding. Period!
- Team should pick more non-functional work to improve the code base
- Each story should be divided & people assigned to it — not everyone on the same story
- Use a more accurate way of estimating story size — what we use isn't accurate
- Need more team-building events

**Action items**
- Try to eliminate unnecessary meetings
- Find more accurate ways to estimate our stories
- Guarantee all stories have clear acceptance criteria before picking them up

No votes, owners, dates. Facilitator note: "sprint missed commitment again".

### Review findings (if this board were submitted as the report)

1. **Actions restate the problem** — "try to eliminate unnecessary meetings", "find more accurate ways" are wishes. Each needs a verb + scope + owner: *"PM audits recurring meetings, proposes cuts at next planning"*.
2. **The headline is hidden in a facilitator note** — "missed commitment again" is the cycle's story, and it's not on the board. Ask for the number (committed vs done) and lead with it.
3. **Three improvement notes share one cause** — unclear acceptance criteria, whole-team swarming on one story, and bad estimates are all *story refinement* failing. One theme, one or two actions — not three.
4. **Venting notes carry signal** — "Less meetings more coding. Period!" is a morale flag. Keep it (blameless, faithful), quantify it (meeting hours / week), don't drop it for tone.
5. **Wins without evidence** — "E2E automation has really improved things": improved what? Suite runtime, escaped defects, release confidence? Ask for one number.
6. **Contradiction to surface** — "mid-sprint meeting to discuss future stories" (went well) vs "less meetings" (improve). Likely both true: *that* meeting works, *others* don't. The meeting audit should name which to keep.
7. **Uncovered items** — tech debt (non-functional work) and team building have no action. Either act or park explicitly.
8. **No previous-retro follow-up** — "missed commitment *again*" implies a prior retro raised it. Find it.

### Produced report (Produce mode output)

**Team:** Checkout Product Squad · **Cycle:** Sprint 2026-S12 (2026-05-29 → 2026-06-11) · **Date held:** 2026-06-12 · **Facilitator:** `[need input]` · **Previous retro:** `[need input]`

#### Summary

The sprint **missed its commitment again (`[need input]`: committed vs done)**, and the team traces it to one pattern: **stories start before they're ready** — no acceptance criteria, no split, estimates that don't hold. The flip side of a good collaborative sprint is too much of it in meetings. Direction: *fix refinement before adding process*.

- **Biggest wins** — E2E automation (`[need input]`: metric), smooth onboarding of a new engineer, strong pairing while remote, team adopting the new stack.
- **Top pain points** — stories not ready when picked up; estimates unreliable; meeting load crowding out focus time.
- **Where the team wants to go** — ready stories, fewer and better meetings, room for tech debt.

#### Previous action items — follow-up
`[need input]` — "missed commitment again" suggests a prior action on planning. Link the previous retro and report its status.

#### What went well
- E2E automation "really improved things" — `[need input]`: runtime, pass rate or escaped defects.
- New team member onboarded well — `[need input]`: time to first merged change.
- Pairing held up remotely.
- Mid-sprint look-ahead on upcoming stories — keep (see Needs improvement: meetings).
- Team willing to adopt the new front-end stack.

#### Needs improvement
**Planning & estimation**
- **Stories start without acceptance criteria → rework and mid-sprint scope questions → no definition of ready** *(cause: suspected)*.
- Whole team swarms one story → idle time and merge conflicts → stories not split before pickup *(same cause)*.
- Estimates miss → commitment missed → sizing done on unrefined stories *(cause: suspected)*.

**Ways of working**
- **Meeting load crowds out coding** (strong feeling on the board) → `[need input]`: meeting hours/week → cause unknown; audit needed.
- Wish for more team-building events.

**Engineering health**
- Non-functional work (tech debt) never gets picked → no capacity reserved *(cause: suspected)*.

#### Start / Stop / Continue
- **Start:** a definition of ready (acceptance criteria + split) checked at refinement.
- **Stop:** pulling unrefined stories into the sprint.
- **Continue:** mid-sprint look-ahead; pairing; investing in E2E automation.

#### Action items

| # | Action item | Theme | Owner | Priority | Due | Success signal |
|---|---|---|---|---|---|---|
| 1 | Agree a definition of ready (AC written, story split, estimated) and enforce it at sprint planning | Planning | `[need input]` (PM) | High | next planning | 0 stories pulled in without AC next sprint |
| 2 | Audit recurring meetings; propose cuts/merges; keep mid-sprint look-ahead | Meetings | `[need input]` | High | 2026-06-26 | Meeting hours / engineer / week down `[need input]`% |
| 3 | Reserve a fixed share of sprint capacity for tech debt | Tech debt | `[need input]` (tech lead) | Med | next planning | Share reserved and delivered, checked at retro |
| 4 | Plan one team event this quarter | Team | `[need input]` | Low | 2026-07-31 | Event held |

Estimation is **not** a separate action: re-check it after #1 — estimates on refined stories may be fine.

**Gaps to fill before closing:** committed vs done number, E2E metric, facilitator, owners, previous retro link.

### Carry-over for next retro

Check: definition of ready (#1) → stories without AC, commitment hit rate · meeting audit (#2) → hours/week · tech-debt capacity (#3) · estimation accuracy after refinement fix.
