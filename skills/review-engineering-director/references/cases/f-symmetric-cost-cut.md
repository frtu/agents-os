---
case: F
name: Symmetric cost cut on a shared platform
shape: A top-down "cut X%" lands on a platform that doesn't own the workloads; the draft plan applies the same % to everyone or has the platform optimize everything itself.
heuristics: [18, 3, 7]
guide: ../guides/cost-and-budget.md
template: ../templates/exec-cost-review.md
---

# Case F — Symmetric cost cut on a shared platform

- **Before:** *"Each team will reduce usage by 20%; the platform will run an optimization program."* There are three pages of tables grouped by team, with no lever types.
- **Common approach:** a uniform percentage cut, or the platform does the optimizing.
- **Why this one diverges:** a uniform cut punishes small, efficient teams as hard as wasteful ones. The platform cannot change other teams' code. A blank-sheet target freezes everyone.
- **Interrogation:** *"Is the burden proportional to the opportunity, and will the bar stay fixed?"* (18). *"Who owns each cost line?"* *"Which levers are easy, which are a redesign, which hit the business?"*
- **What surfaces:** a few items hold most of the spend. Some "savings" just move cost between teams. The exec can always say "turn it off". Your job is to give him focus points, not raw data.
- **Distilled (what to do):** WHO / HOW / WHEN. One owner per line. Levers on a green / light-orange / dark-orange / red scale. Pareto batches. One high bar, not moved; aggressive internally, realistic in the report. An asymmetric burden. Each team gets duty and ability: its own breakdown plus suggested actions. The fastest team's approach becomes best practice. Showback in public. Swap, don't add. The exec holds the whip; the platform holds the strategy.
- **Lesson:** "symmetric is stupid, asymmetric is real". One chart (cost units sorted by size, colored by lever type, before and after) beats every table.
