# Template: Interview Question Guide

Output: `{candidate folder}/2-{step}-questions-{slug}.md`.

This is the **generic** guide. If `references/steps/{step}.md` exists, it overrides the question mode, the categories and the interview shape, and supplies the block for the `{Step-specific section}` slot.

How to fill it:
- Durations come from the step page. Recommendation bands come from the step rubric (vault map → Step pages / Step rubrics).
- The leveling rows are the same as in the candidate page's leveling table.

```markdown
---
Category: projects
Tags: [hiring, {step}, candidate, {slug}, {product}, {target-level}, interview-guide]
Source links:
  - [[1-candidate-{slug}]]
  - [[source-{slug}]]
  - [[{step rubric}]]
  - [[{step page}]]
Created: {date}
Last Updated: {date}
---

# {Step} Guide: {Full Name}

Tailored {step} question bank for [[1-candidate-{slug}|{Full Name}]] ({Target} {Title} candidate, {Product}).

## Calibration Framing

### {Target} Expectations — What "Yes at {Target}" requires (and where {Stretch} begins)

| Dimension | [[role-{track}-{floor}\|{Floor}]] baseline | **[[role-{track}-{target}\|{Target}]] must show** | [[role-{track}-{stretch}\|{Stretch}]] stretch |
|-----------|------------------|-----------------------|------------------|
| {Dimension} | ... | **...** | ... |

{Same rows as the candidate page's leveling table, without the "Current signal" column. If the step rubric has a level calibration table (expected score per level), add one line: "Rubric expects {score} at {Target}, {score} at {Stretch}."}

### Risk Profile (from prior rounds)

**Confirmed strengths:**
- {Prior score + interviewer, with the concrete behavior observed}

**Open concerns to probe:**
- **{Central concern}** — {verbatim quote}. **The single most important signal to resolve this round.**
- {Other concern} — {one line}

> **Interviewer note.** {The specific way this candidate could pass the round without being tested — e.g. "résumé so aligned the failure mode is a comfortable retrospective". Tell the interviewer how to force them onto new ground and demand numbers, not nouns.}

{Step-specific section: insert the block defined in `references/steps/{step}.md` (e.g. Primary Challenge, Gap Routing). Omit if there is none.}

## Question Bank (Tailored to Resume)

### A. {Category} — {Focus}

*Focus: {one line — what this category decides for this candidate}*

1. **"{Question as you would say it aloud to the candidate}"**
   - *Listening for:* {concrete content of a good answer — nouns, mechanisms, numbers}
   - *{Target} signal:* {the behavior that separates {Target} from {Floor}; tie to a resume claim or concern where possible}

2. **"{Question}"**
   - *Listening for:* ...
   - *{Target} signal:* ...

### B. {Category} — {Focus} — **CRITICAL FOCUS**

{Mark the 1-2 categories that carry the central probe with **CRITICAL FOCUS**.}

{5-7 categories, 3-5 questions each, unless the step file says otherwise. Start from the step page's question bank and the rubric's probing questions, then tailor. Number questions **continuously Q1…Qn across all categories** (not A1, B1) so the flow, red-flag and signal tables can cite them.}

## Recommended Interview Flow ({duration} min)

| Time | Section | Top Picks | Purpose |
|------|---------|-----------|---------|
| 0–5 min | Warmup / {…} | Q1, Q2 | {Purpose} |
| 5–15 min | {Category} | Q{n}, Q{n} | {Purpose — **bold the critical sections**} |

*Pick {N} in the flow; Q{x}, Q{y}, … are backups by theme.*

{Use cumulative time ranges; the last range must end exactly at {duration}. Give the most minutes to the CRITICAL FOCUS categories.}

## Red Flags to Watch For

{Start from the step page / rubric red flags; make each specific to this candidate.}

| Question | Red Flag | What It Indicates |
|----------|----------|-------------------|
| Q{n} / Q{m} | {Observable pattern} | {Which concern it confirms — bold the central one} |

## Positive Signals to Confirm "Strong Yes" (and open the {Stretch} conversation)

- {Observable behavior, ideally "unprompted"} ({which concern it rebuts})
- {Behavior that signals {Stretch}} → **{Stretch} signal**

## Decision Framework

{One row per band in the step rubric's Recommendation Bands, using its labels and thresholds. Map each band to a level outcome: stretch / target / floor / no.}

| Recommendation | Threshold | Level outcome | When to Apply |
|----------------|-----------|---------------|---------------|
| **{Top band}** | {from rubric} | {Target}; open {Stretch} | {Concrete, candidate-specific criteria} |
| **{Band}** | {from rubric} | {Target} | {Criteria} |
| **{Band}** | {from rubric} | down-level {Floor} | {Criteria — usually "central concern persists / interviewer-steered"} |
| **{Bottom band}** | {from rubric} | No | {Criteria} |

## Scoring Reminder

Score against [[{step rubric}|the {Step} rubric]] ({criteria + weights in one line, from the rubric}). If the rubric is marked preliminary or has a variant (e.g. an AI-enabled format), say so and name the instrument to use. Close with one bolded line: **{Target} key differentiator for {First Name}:** {what they have clearly shown already} — the round decides {the 1-2 open questions}.

## Related

- [[1-candidate-{slug}|Candidate Evaluation: {Full Name}]]
- [[source-{slug}|Source: {Full Name} Profile]]
- [[{step page}|{Step} Interview Step]] · [[{step rubric}|{Step} Rubric]]
- {Challenge / team-specific interview page used, if any}
- [[role-{track}-{target}|{Target} {Title}]] · [[role-{track}-{stretch}|{Stretch} {Title}]]
```
