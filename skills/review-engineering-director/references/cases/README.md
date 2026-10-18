# Worked Case Studies — index

The reference library behind `SKILL.md`: **cases** (recurring shapes), **theme guides** (playbooks by topic) and **templates** (artifacts to produce). It is generic on purpose: pattern-match the shape, not the specifics.

**Loading rule:** read this README first, then load **only** the files that match the doc or situation. That usually means one case and at most one guide, plus one template in Produce mode. Never read the whole library up front OR delegate selection to sub agents.

## Where the library comes from

- **Cases A–D** come from coaching on executive proposals and senior promotion packets. They are *doc-level* failures: what a weak claim looks like on the page.
- **Cases E–S** come from about real life example. They are *situation-level* failures: what a weak move looks like in a meeting or plan. They add **Common approach → Why this one diverges → What to do**, so the skill can say when the textbook answer is not enough.

## Cases

### Doc-level shapes (Review / Adversarial modes)

| Case | Shape to match | File |
| ---- | -------------- | ---- |
| A | Product-definition / vision doc: expansive capability catalog, no wedge, no explicit ask | `a-product-definition.md` |
| B | Commodity-looking work (migration, upgrade, refactor) claimed by category or output count | `b-commodity-migration.md` |
| C | A flat list of equal-weight bullets with no thesis | `c-bullet-point-pile.md` |
| D | Raw volume (MR count, tickets, hours) offered as proof of seniority | `d-effort-vs-seniority.md` |

### Leadership-situation shapes (Coaching mode, and any doc about these situations)

| Case | Shape to match | Heuristics | File | Guide |
| ---- | -------------- | ---------- | ---- | ----- |
| E | Exec judges the vision from a narrow increment ("wrong direction, think bigger") | 15, 20, 13 | `e-vision-read-from-a-milestone.md` | exec-review-and-demo |
| F | Top-down cost cut applied symmetrically, or the platform optimizes everyone's spend | 18, 3, 7 | `f-symmetric-cost-cut.md` | cost-and-budget |
| G | Prepaid budget burned early; nobody owned the tool; past blame mixed with next year's ask | 19, 4, 16 | `g-cost-crisis-no-owner.md` | cost-and-budget |
| H | Partner proposes a "unified platform" with no owner, wants your groundwork or fine-grained APIs | 19, 16, 15 | `h-partner-owns-the-vertical.md` | platform-boundary-and-partners |
| I | Stakeholder says "it doesn't work"; the team answers with more tests and dashboards | 22, 1, 3 | `i-perception-vs-tests.md` | stakeholder-trust-and-sign-off |
| J | Every function must sign; dense matrix, or the platform owns go/no-go | 22, 19, 7 | `j-sign-off-sprawl.md` | stakeholder-trust-and-sign-off |
| K | Request phrased as a solution ("global score", "syntax X", "make it 1000") | 16, 20, 2 | `k-dictated-how.md` | stakeholder-trust-and-sign-off |
| L | New hands-on boss; first 1:1 is a roadmap or "all is stable" | 21, 16, 8 | `l-new-boss.md` | managing-up |
| M | Strategic vendor under finance review; plan is price squeeze or a uniform usage cut | 18, 21, 3 | `m-vendor-under-pressure.md` | cost-and-budget |
| N | High output, low outcome; late nights; many seeds, few harvests | 12, 17, 3 | `n-output-without-outcome.md` | team-load-and-delegation |
| O | Asked to absorb another team's manual ops loop (alert relay, capacity bumps) | 19, 17 | `o-toil-takeover.md` | team-load-and-delegation |
| P | One party lags in a cross-team delivery; its scope is spread across everyone | 19, 17, 1 | `p-everyone-shares-the-bill.md` | team-load-and-delegation |
| Q | Annual forecast extrapolated from last year's imposed number | 4, 18, 10 | `q-budget-forecast.md` | cost-and-budget |
| R | Leaders asked "should we go?"; the doc is an action plan | 15, 20, 13 | `r-plan-instead-of-risk.md` | exec-review-and-demo |
| S | Continue/stop/start review that lists generic faults or punishes a signature strength | 12, 17, 9 | `s-mid-year-feedback.md` | performance-and-1on1 |

**Case file structure.** Frontmatter has `case`, `name`, `shape` and `heuristics`, plus optional `guide` and `template`. The body runs **Before** (the weak claim or move) → **Common approach** → **Why this one diverges** → **Interrogation** (the challenge to fire, with heuristic numbers) → **What surfaces** → **Distilled (what to do)** → **Lesson**. Cases A–D predate the Common/Diverges lines and omit them.

## Theme guides — `../guides/`

Load one when the doc or situation is mainly about the theme. Each guide has: *Load when* → *Default moves* → *Questions to fire* → *Traps* (some add *Signals* or *Morale*).

| Guide | Theme | Cases |
| ----- | ----- | ----- |
| `exec-review-and-demo.md` | Exec demos, vision refresh, risk assessments, debriefs | E, R |
| `cost-and-budget.md` | Cost mandates, finance reviews, forecasts, vendor spend, overspend crises | F, G, M, Q |
| `platform-boundary-and-partners.md` | Co-build negotiations, platform scope, custom asks, adoption | H |
| `stakeholder-trust-and-sign-off.md` | Distrust, quality bars, definition of done, multi-party sign-off, dictated HOWs | I, J, K |
| `team-load-and-delegation.md` | Overload, delegation design, toil takeover, cross-team lag, AI use | N, O, P |
| `performance-and-1on1.md` | Reviews, promotion and comp talks, 1:1 structure | S |
| `managing-up.md` | New boss, method misalignment, reorg offers | L |
| `interviewing.md` | Director lens on hiring interviews | — |

## Templates — `../templates/`

Use in **Produce mode**, or as a checklist in **Review mode**.

| Template | Artifact | Cases |
| -------- | -------- | ----- |
| `product-definition.md` | Product-definition / vision proposal with an ask | A |
| `vision-refresh.md` | Re-presenting the vision to an exec | E |
| `exec-cost-review.md` | Response to a cost mandate or finance review | F, G, M, Q |
| `risk-assessment.md` | "Should we go?" evaluation | R |
| `mid-year-review.md` | Continue / stop / start review | S |

## Heuristic quick map

Numbers refer to the table in `SKILL.md`. Heuristics 1–14 are doc judgement. 
15–22 come from the day to day example: **15** two audiences · **16** for what before how · **17** decompose the WHEN · **18** one high bar, asymmetric burden · **19** a named owner, not a proxy · **20** show limits · **21** value → cost → migration · **22** fear is solved by tangible data.

## Growing the library

When you hit a **new recurring shape** that no case above captures, add it here so future runs reuse it, **without touching SKILL.md**:

1. Confirm it is genuinely new (not a variant of an existing case) and worth reusing. A variant goes into the existing case's *What surfaces* or the relevant guide instead.
2. Write `{next-letter}-{short-name}.md` in this folder (next letter: **T**). Use the frontmatter and body structure above, including *Common approach* and *Why this one diverges* for situation cases.
3. Add one row to the right index table, with its heuristics and guide.
4. If it opens a new theme, add a guide in `../guides/` and a row to the guides table here. Add the guide to SKILL.md's guide table too; that is the only reason to edit SKILL.md.
5. Keep it **generic**: no real names, companies, vendors, projects or numbers. Turn the specifics into roles ("a partner team", "a senior exec", "a workflow vendor") and shapes.
