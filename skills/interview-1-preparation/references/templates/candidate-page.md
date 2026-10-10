# Template: Candidate Evaluation Page

Output: `{candidate folder}/1-candidate-{slug}.md` (folder from [vault-map](../vault-map.md) → Outputs).

How to fill it:
- `{…}` are placeholders. Text in `{…}` that is a full sentence is an instruction and must be replaced, not kept.
- Level codes, dimension names, bucket names and step links come from the vault pages listed in the vault map. Never invent them.
- `{Floor}` / `{Target}` / `{Stretch}` are the level codes decided in SKILL.md step 3b.

```markdown
---
Category: projects
Tags: [hiring, candidate, evaluation, {product}, {target-level}, {step}]
Source links:
  - [[source-{slug}]]
Created: {date}
Last Updated: {date}
---

# Candidate Evaluation: {Full Name}

**Role:** {Title} ({Target})
**Team:** {Product}
**Interview Steps:** {one wikilink per step in the hiring process that applies to this req, in order, e.g. [[step-hire-{n}-{name}|{Name}]] | …} | [[2-{step}-questions-{slug}|{Step} Guide]]
**Status:** Pre-Interview

## Candidate Profile

| Attribute | Details |
|-----------|---------|
| **Current Role** | {Role} @ {Company} |
| **Experience** | {X}+ years |
| **Education** | {Degree}, {School} |
| **Location** | {City} ({Visa/Citizenship if relevant}) |
| **Target Level** | {Target} ({Title}), floor {Floor}, stretch {Stretch} |

## Background Summary

> "{Verbatim 1-2 sentences from the resume summary — do not paraphrase inside the quote}"

{2-3 sentences in your own words: what they built, with the 2-3 biggest numbers, and which JD/mission line it maps to — link the JD or hiring page.}

## Experience Highlights

### {Company} ({Dates}) — {Title}

- **{Theme}** — {Accomplishment with metrics}
- **{Theme}** — {Accomplishment}

{Repeat for each relevant role}

## Strengths ({Product} Fit)

### {Strength Category}
{Evidence from resume with metrics. Why it matters for the role.}

## Weaknesses (Areas to Probe)

### {Concern} — **the central round load**
{Quote the source of the concern verbatim (recruiter / prior interviewer). Why it matters against a specific JD line. How this round tests it. End with **Highest-priority probe.**}

### {Concern}
{Why / how to probe. If partial counter-evidence exists, name it — "partially rebutted by X, needs depth verification".}

### {Concern} (route to {Later Step})
{Concerns this round cannot resolve: one line, then **Not this round's job — flag for {step}.**}

## Role Match Analysis

| {Product} Requirement | Candidate Evidence | Fit |
|-----------------------|-------------------|-----|
| **{Requirement from the JD}** | {Evidence} | Strong/Probe/Gap |

## Pre-Interview Assessment

{One row per bucket of the vault's assessment framework (vault map → Assessment framework). Use its bucket names and order.}

| Bucket | Assessment | Priority |
|--------|------------|----------|
| {1. Bucket name} | {Strong/Probe/Gap} — {reason} | {Low/Medium/High} |

## {Target} Leveling (with {Stretch} stretch)

### What "Yes at {Target}" requires — and where {Stretch} begins

{One row per dimension of the track's competency ladder (vault map → Competency ladders). Pull cell text from the ladder and role pages.}

| Dimension | [[role-{track}-{floor}\|{Floor}]] baseline | **[[role-{track}-{target}\|{Target}]] must show** | [[role-{track}-{stretch}\|{Stretch}]] stretch | Current signal |
|-----------|------------------|-----------------------|------------------|----------------|
| {Dimension} | {from ladder/role page} | **{from ladder/role page}** | {from ladder/role page} | {≤15 words: evidence + what is unvalidated} |

{"Current signal" cells stay short. Put reasoning in prose under the table.}

### Leveling Decision Questions (answer after the round)

{4-5 questions **specific to this candidate**, each a binary that maps to floor / target / stretch. Pattern:}
1. Did they {do the thing the central probe tests}, or {the failure mode the concern predicts}?
2. Did they **set** {named platform}'s direction and drive its adoption, or **execute** a direction handed to them?
3. Is {their biggest scope claim} evidence of **{Stretch}-shaped** or **{Target}-shaped** ownership?
4. {Build-vs-buy / context-fit question grounded in the team's real stack}
5. Is {their strongest asset} **production-hardened** or an impressive exploration?

## Recommendation

**{Action} — anchor the round on {the central probe}.**

{One paragraph: why this candidate matters (strongest asset, prior scores), the 1-2 questions that decide floor vs target vs stretch, what the round must contain, then **conditional outcomes**: "If {X} *and* {Y}, a {Stretch} conversation is warranted; if {failure mode}, land at {Target} (or {Floor}) and route {Z} to {later step}." Never predict the outcome: prior scores inform the load, they do not decide it in advance.}

## Related

- [[source-{slug}|Candidate Profile]] — Full source materials
- {[[jd-…\|JD]] or [[interviews-{product}\|{Product} Hiring]] — whichever exists}
- [[role-{track}-{target}|{Target} {Title}]] — Target level · [[role-{track}-{stretch}|{Stretch} {Title}]] — Stretch level
- [[2-{step}-questions-{slug}|{Step} Interview Guide]] — Tailored questions
```
