# Pitch & Pain-Point Cases — index

The reference library behind `SKILL.md` for **product presentations / pitches** and **pain-point evidence**: **cases** (recurring failure shapes), **theme guides** (playbooks by topic) and **templates** (artifacts to fill or score against). It is generic on purpose: pattern-match the shape, not the specifics.

**Loading rule:** read this README first, then load **only** the files that match the doc or situation — usually one case and at most one guide, plus one template in Prepare mode or as a review checklist. Never read the whole library up front. Strategy-level critique (6 strategic questions, competitors, coherence, unit economics, bullseye) stays in `../product-strategy-critique-methodology.md`.

## Where the library comes from

- YC Startup Library: Michael Seibel (investor vs customer pitch), Aaron Harris (seed deck), Janelle Tam (Series A pitch and deck), Kevin Hale (deck design).
- StartupFundraising.com teardown of an 11-slide deck attributed to Peter Thiel (persuasion arc, build order, slide dependencies) — attribution unverified.
- Customer-discovery practice (past-behaviour questions, workarounds, commitments) — general practice, not from the clippings.

Long form lives in the management Obsidian vault: `wiki/concepts/technologies/pitch.md`, the *Pitching & persuasion* patterns, `wiki/people/processes/pitch-preparation.md` (7 steps) and `output/templates/pitch-template.md`.

## Cases

| Case | Shape to match | Checks | File | Guide |
| ---- | -------------- | ------ | ---- | ----- |
| A | Same deck for customers and investors/execs: jargon, screenshots, feature depth | P1, P2, P10 | `a-one-pitch-for-everyone.md` | pitch-narrative-and-structure |
| B | Abstract slogan instead of a one-liner anyone can picture | P2, P1 | `b-slogan-one-liner.md` | pitch-narrative-and-structure |
| C | Problem = the whole industry; no slice, no payer, no current workflow | P3, P5 | `c-problem-too-big.md` | pain-points-and-evidence |
| D | Solution = screenshot, feature list or roadmap; no quantified before/after | P4, P8, P10 | `d-feature-tour-solution.md` | pitch-narrative-and-structure |
| E | Number dump: many KPIs, cumulative charts, double axes, undefined metrics | P6, P10 | `e-number-dump.md` | metrics-and-traction |
| F | Vision / roadmap first; what's built appears late or never | P8, P4, P6 | `f-vision-before-credibility.md` | pitch-narrative-and-structure |
| G | Top-down market ("$1T", "every team will use it") | P7 | `g-top-down-market.md` | metrics-and-traction |
| H | Pain evidence = opinions, hypothetical surveys, demo compliments | P5, P3 | `h-opinions-as-evidence.md` | pain-points-and-evidence |
| I | No ask, or the ask doesn't match what blocks growth | P11, P8 | `i-missing-ask.md` | pitch-narrative-and-structure |
| J | Slide overload: many ideas per slide, dense, diagrams; no questions asked | P10, P12 | `j-slide-overload.md` | rehearsal-and-delivery |

**Case file structure.** Frontmatter has `case`, `name`, `shape`, `checks`, plus optional `guide` and `template`. The body runs **Before** → **Common approach** → **Why this one diverges** → **Interrogation** (the challenge, with check numbers) → **What surfaces** → **Distilled (what to do)** → **Lesson**.

## Theme guides — `../guides/`

Each guide has: *Load when* → *Default moves* → *Questions to fire* → *Traps* (some add *Signals of success*, an evidence table or a mapping).

| Guide | Theme | Cases |
| ----- | ----- | ----- |
| `pitch-narrative-and-structure.md` | Audience, spine, slide order, credibility → vision, the ask, internal-initiative mapping | A, B, D, F, I |
| `pain-points-and-evidence.md` | Discovery interviews, workarounds, existing signals, evidence strength, testimonials | C, H |
| `metrics-and-traction.md` | Hero facts, trends, metric definitions, unit economics, bottoms-up market | E, G |
| `rehearsal-and-delivery.md` | Slide clarity, flash test, 20/20/20 practice, video, daily refinement | J |

## Templates — `../templates/`

| Template | Artifact | Cases |
| -------- | -------- | ----- |
| `pitch-deck.md` | Spine + slide outline for a pitch / product presentation | A, B, D, F, I |
| `pain-point-evidence-log.md` | Pain points, testimonials, metrics, hero facts, Q&A bank | C, H |
| `customer-interview-guide.md` | 30-min discovery script + notes | H |
| `pitch-review-scorecard.md` | P1–P12 scoring + post-pitch debrief | all |

## Check quick map

Numbers refer to the **Pitch Checks** table in `SKILL.md`: **P1** audience-fit · **P2** concrete one-liner · **P3** problem slice from the payer · **P4** quantified before/after · **P5** past-behaviour evidence · **P6** hero facts · **P7** bottoms-up market · **P8** credibility before vision · **P9** insight, moat, why now · **P10** legible/simple/obvious · **P11** explicit ask · **P12** overview + appendix.

## Growing the library

When you hit a **new recurring shape** no case captures, add it **without touching SKILL.md**:

1. Confirm it is genuinely new (not a variant). A variant goes into the existing case's *What surfaces* or the relevant guide.
2. Write `{next-letter}-{short-name}.md` here (next letter: **K**) with the frontmatter and body structure above.
3. Add one row to the Cases table with its checks and guide.
4. If it opens a new theme, add a guide in `../guides/`, a row to the guides table here, and to SKILL.md's guide table (the only reason to edit SKILL.md).
5. Keep it **generic**: no real names, companies, products or numbers — roles and shapes only.
6. Mirror significant additions to the management vault's pitch pages.
