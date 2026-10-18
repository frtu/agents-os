# Template — Exec cost review (mandate response / finance review)

Use for a response to a top-down cost target, a finance review of a vendor, or an overspend explanation. Pairs with Cases F, G, M, Q and `../guides/cost-and-budget.md`.

```markdown
# [Tool/vendor] cost: [commitment in one line, e.g. "−X% by <date>, Y% already actioned"]

**Bottom line:** [Committed reduction + confidence + the one decision we need from you.]

## Where the money goes  (ONE chart)
[Each cost unit as a bar, sorted by size; color = lever type; before/after overlay.
 Caption: "Top N items = X% of spend."]

## Levers, by risk
| Lever | Scale | Est. impact | Confidence | Owner | When |
|---|---|---|---|---|---|
| [close unused envs] | Green | | 80% | | |
| [retention/config] | Light orange | | | | |
| [redesign] | Dark orange | | | | |
| [cut a feature] | Red — not proposed | | | | |

## How the target is distributed
[Asymmetric rule in one line: who carries more and why. The bar does not move.]

## Governance from here
- Owner of the tool: [name/role]
- Baseline: [growth % for everyone]; extra = request + justification
- Visibility: showback per team, alerts at 80/90/100% of quota
- Enforcement: [not yet / when / who decides]

## What we're giving up
[Velocity cost of dark-orange items; risk accepted.]

## Asks
[Exec relay to non-responsive teams? Vendor negotiation levers? Approval of the baseline?]
```

**Section insight**
- One chart beats tables. The exec can push but cannot guess what to do next, so give him the focus points.
- Every number carries a confidence. "I prefer no number to a wrong number."
- Moving cost between teams is not a saving; say so before finance does.
- Start the chart simple and add the overlay once the reader knows the graph.
