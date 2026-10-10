# Step: Engineering Screen (Step 1b)

Loaded by `SKILL.md` when `{step}` is `engineering-screen`. Overrides the generic question guide (SKILL.md step 6) where stated.

**Gate:** runs **only for IC lvl 4+ or Manager lvl 2+ reqs**. If the target level is below that, do not offer this step.

**Read first:** [[step-hire-1b-engineering-screen|Step 1b]] and [[interview-rubric-engineering-screen|Engineering Screen Rubric]].

## What changes vs the generic guide

| Aspect | Other steps | Engineering Screen |
|--------|-------------|--------------------|
| Question mode | Hypothetical / live problem | **Retrospective**: dig into systems the candidate actually shipped |
| Source of questions | Rubric criteria | **The candidate's own résumé claims**, one deep dive per claim |
| Second deliverable | — | **Gap-routing list**: each gap named and assigned to a downstream stage |
| Roadmap | Not referenced | Guide must name **the live roadmap problems** their experience maps onto |

## Assessment areas

From [[source-hiring-stage-engineering-screen|the stage brief]]. Every area must be covered by at least one category below.

1. Strategic Thinking & Problem Solving
2. Leadership & Influence
3. Technical Depth
4. Communication & Executive Presence
5. Growth & Ownership Mindset
6. Motivation & Alignment
7. AI Mindset

## Question categories

These replace the generic 5-7 categories:

- **Background & Motivation**: why now, why this domain
- **Deep Dive: Mechanism**: pick 2-4 shipped systems from the résumé; ask *how it actually worked*, not what it did
- **Deep Dive: Scale & Impact**: force numbers (rows, QPS, teams onboarded, cost delta)
- **Deep Dive: Where It Broke**: the failure they own; the limit they hit
- **Strategic Framing & Executive Presence**: can they pitch the system to a non-engineer in two sentences
- **Roadmap Mapping & Build-vs-Buy**: put a real open problem in front of them
- **AI Mindset**: do not ask a canned tooling question. **Mine it from the deep dives**: where did they reach for a model because conventional analysis failed?
- **Candidate Questions (Scored)**: what they ask reveals what they think matters

**Interview shape:** ~45 min: 5 background / 25 deep dives / 10 roadmap mapping / 5 candidate questions.

## Step-specific section

Insert at the `{Step-specific section}` slot of the question guide:

```markdown
## Gap Routing

| Gap | Why this round can't close it | Route to |
|-----|-------------------------------|----------|
| {Gap} | {reason} | [[step-hire-{n}-{step}\|{Step}]] |
```

## Red flag to pre-load

Depth that evaporates one layer below the architecture diagram. Every deep dive needs a prepared "and how did that work underneath?" follow-up.

> **Caveat:** this stage is **PRELIMINARY**: weights and scale bounds are unconfirmed. Do not present its scores as calibrated.

## Checklist additions

- [ ] 2-4 deep dives, each anchored on a named résumé claim, each with an "underneath" follow-up.
- [ ] All 7 assessment areas are covered.
- [ ] Gap Routing table present; every gap names a downstream step.
