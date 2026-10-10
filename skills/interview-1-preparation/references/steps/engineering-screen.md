# Step: Engineering Screen

Relevant when `{step}` is `engineering-screen`. Overrides the generic question guide where stated.

**Gate:** conditional step. Offer it only if the target level passes the step page's **Applies to** line.

**Read first** (vault map → Step key → vault pages): the step page (purpose, *What It Is Not*, assessment areas, interview shape, question bank, gap routing, red flags) and its rubric (marked as preliminary or not, evidence patterns, level calibration). Its source brief lists the assessment areas.

## Core rule

This round is **retrospective**: dig into systems the candidate actually shipped, one deep dive per résumé claim. The most common failure is drifting into hypothetical design, which is the system step's job.

## What changes vs the generic guide

| Aspect | Generic guide | Engineering Screen |
|--------|---------------|--------------------|
| Question mode | Tailored to résumé | **Retrospective deep dives** on the candidate's own claims |
| Source of questions | Rubric criteria | Each deep dive anchored on a **named résumé claim** |
| Extra deliverable | — | **Gap Routing** table, the step's second output |
| Roadmap | Not referenced | Name **the live roadmap problems** their experience maps onto |

## Question categories

Take the categories and their order from the step page's **Question Bank** headings, and make sure every **assessment area** on the step page is covered by at least one category. Tailoring rules:

- **Deep dives:** at most as many systems as the step page's interview shape allows. Go mechanism → scale (force numbers) → where it broke.
- **Every deep dive** needs a prepared "and how did that work underneath?" follow-up.
- **AI mindset (if it's an area):** don't ask a canned tooling question. Mine it from the deep dives: where did they reach for a model because conventional analysis failed?
- **Candidate questions are scored.** Keep a slot for them.

**Interview shape:** use the step page's *Interview Shape* table as the flow skeleton (segments and minutes).

## Step-specific section

Insert at the guide's `{Step-specific section}` slot. Take the gap kinds and the target steps from the step page's gap-routing table:

```markdown
## Gap Routing (pre-loaded hypotheses)

| Gap | Why this round can't close it | Route to | What that step should test |
|-----|-------------------------------|----------|----------------------------|
| {Gap specific to this candidate} | {reason} | [[step-hire-{n}-{name}\|{Step}]] | {test} |
```

## Red flag to pre-load

Depth that evaporates one layer below the architecture diagram.

If the rubric is marked preliminary, say so in the Scoring Reminder and don't present its scores as calibrated.

## Checklist additions

- [ ] Each deep dive is anchored on a named résumé claim and has an "underneath" follow-up.
- [ ] Every assessment area on the step page is covered.
- [ ] Gap Routing table present; every gap names a downstream step from the step page's routing table.
