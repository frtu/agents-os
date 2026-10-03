---
name: interview-1-preparation
description: >
  Pre-interview preparation skill. Creates candidate source page with profile analysis,
  strengths/concerns assessment, and tailored interview questions. Use when the user
  says "prepare for interview", "pre-interview {name}", or wants to prep before meeting a candidate.
allowed-tools: Bash Read Write Edit Glob Grep AskUserQuestion
---

# Interview Preparation (Pre-Interview)

Create comprehensive candidate evaluation materials with profile analysis, leveling assessment, and tailored interview questions.

## Input

Raw materials in: `raw/People/Candidates/{Candidate Name}/`

Required files:
- Resume (PDF or Markdown) — Experience, skills, education

Optional files:
- Interview briefing — Role context, team, hiring manager
- LinkedIn profile — Current role, tenure
- Recruiting intake form — Success metrics, challenges
- Previous feedback — Prior interview rounds

## Output Structure

```
wiki/projects/product-{product}/_interviews_/
└── candidate-{slug}/
    ├── 1-candidate-{slug}.md          # Candidate evaluation page
    └── 2-{step}-questions-{slug}.md   # Interview guide with tailored questions
```

Also creates/updates:
- `wiki/sources/source-{slug}.md` — Raw profile source
- Product page candidate pipeline table
- `wiki/portal.md` candidate evaluations section
- `wiki/log.md`

## Workflow

### 1. Gather Context

**Question 1: Product/Team**
> "Which product/team is this candidate interviewing for?"

List all projects from `wiki/projects/` as options. User can select one or provide a new product name.

**Question 2: Role and Level**
> "What role and level is this candidate interviewing for?"

Examples:
- "Senior Software Engineer, Product (IC Level 3)"
- "Engineering Lead, Product (Manager Level 1)"

For IC {Level} evaluated vs {Level+1} level range: "Level {Level}-{Level+1} evaluation" — skill generates leveling comparison.

**Question 3: Interview Step**
> "Which interview step are you preparing for?"

Options: `engineering-screen`, `coding`, `system-design`, `hiring-manager` or `team-match`, `bar-raiser`

`engineering-screen` maps to [[step-hire-1b-engineering-screen|Step 1b]] and runs **only for IC lvl 4+ or Manager lvl 2+ reqs**. If the target level from Question 2 is below IC lvl 4 or Manager lvl 2, do not offer it. See "Engineering Screen Preparation" below for how prep differs.

**Question 4: Focus Areas (Optional)**

Check previous feedback for any identified concerns or strengths. Ask:

> "Any specific areas you want to probe? Leave blank for standard assessment."

### 2. Read Raw Materials

For each file in the candidate folder:

| File Type           | What to Extract                                                      |
| ------------------- | -------------------------------------------------------------------- |
| **Resume PDF**      | Experience timeline, skills, education, accomplishments with metrics |
| **Resume Markdown** | Same as above, but in Markdown format                                |
| **Briefing**        | Role context, hiring manager, team structure, interview panel        |
| **LinkedIn**        | Current role, tenure, career trajectory                              |
| **Intake form**     | Success metrics, challenges, interview focus areas                   |

### 3. Find Related Wiki Pages

Look for existing pages to link:
- Role definition: `wiki/people/roles/role-{track}-{level}.md`
- Interview step: `wiki/people/steps/step-hire-{n}-{name}.md`
- Rubric: `wiki/resources/artifacts/interview-rubric-{step}.md`
- Competencies: `wiki/people/competencies/{competency}.md`
- Interview guide (synthesis): `wiki/synthesis/{step}-{level}-{domain}.md`
- Question bank: `wiki/resources/artifacts/{step}-question-bank.md` — reuse its problems/probes as a base
- Rubric variants: `wiki/resources/artifacts/rubric-{step}-*.md`, `rubric-fork-{step}.md` — name which instrument to score with
- Stretch/floor levels: `wiki/people/roles/role-{track}-{level±1}.md`
- Other candidates' evaluations in the same product — any comparison ("same gap as X") **must be a wikilink** to that candidate's page, never a bare first name

### 3b. Decide the Round's Load (before writing anything)

Write down, for yourself, these four answers. Every section of both output files must serve them:

1. **Floor / target / stretch level** — target = recruiter-suggested level (else Question 2); floor = target−1; stretch = target+1.
2. **The single highest-priority probe** — usually the recruiter's or prior interviewer's named concern. Quote it verbatim.
3. **The candidate's strongest asset** for this role (the JD/mission line it maps to).
4. **What is NOT this round's job** — concerns to route to a later step (name the step).

For `system-design`, the primary challenge must sit at the **intersection of (2) and (3)**: built on the asset, but forcing the flagged gap.
- Product interviews: `wiki/projects/product-{product}/interviews-{product}.md`

### 4. Create Output Directory

```bash
mkdir -p wiki/projects/product-{product}/_interviews_/candidate-{slug}
```

### 5. Create Candidate Evaluation Page

Write `wiki/projects/product-{product}/_interviews_/candidate-{slug}/1-candidate-{slug}.md`:

```markdown
---
Category: projects
Tags: [hiring, candidate, evaluation, {product}, {level}, {step}]
Source links:
  - [[source-{slug}]]
Created: {date}
Last Updated: {date}
---

# Candidate Evaluation: {Full Name}

**Role:** {Title} ({Level})
**Team:** {Product}
**Interview Steps:** [[step-hire-1-recruiter|Recruiter]] | [[step-hire-2-coding|Coding]] | [[step-hire-3-system|System Design]] | [[{step}-questions-{slug}|{Step} Guide]]
**Status:** Pre-Interview

## Candidate Profile

| Attribute | Details |
|-----------|---------|
| **Current Role** | {Role} @ {Company} |
| **Experience** | {X}+ years |
| **Education** | {Degree}, {School} |
| **Location** | {City} ({Visa/Citizenship if relevant}) |
| **Target Level** | {Level} ({Title}) |

## Background Summary

> "{Verbatim 1-2 sentences from the resume summary — do not paraphrase inside the quote}"

{2-3 sentences in your own words: what they built, with the 2-3 biggest numbers, and which JD/mission line it maps to — link the hiring page.}

## Experience Highlights

### {Company} ({Dates}) — {Title}

- **{Theme}** — {Accomplishment with metrics}
- **{Theme}** — {Accomplishment}
...

{Repeat for each relevant role}

## Strengths ({Product} Fit)

### {Strength Category}
{Evidence from resume with metrics. Why it matters for the role.}

### {Strength Category}
...

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
| **{Requirement}** | {Evidence} | Strong/Probe/Gap |
...

## Pre-Interview Assessment

### 5 Buckets Framework

| Bucket | Assessment | Priority |
|--------|------------|----------|
| 1. Problem Solving | {Strong/Probe/Gap} — {reason} | {Low/Medium/High} |
| 2. Leadership & Strategy | {Assessment} | {Priority} |
| 3. Operational Excellence | {Assessment} | {Priority} |
| 4. Culture & Collaboration | {Assessment} | {Priority} |
| 5. Talent & Team Building | {Assessment} | {Priority} |

## {Target} Leveling (with {Stretch} stretch)

Always bracket the target: floor (target−1) / target / stretch (target+1). Tag the file with the **target** level only (e.g. `p4`), not a range.

### What "Yes at {Target}" requires — and where {Stretch} begins

| Dimension | [[role-{track}-{floor}\|{Floor}]] baseline | **[[role-{track}-{target}\|{Target}]] must show** | [[role-{track}-{stretch}\|{Stretch}]] stretch | Current signal |
|-----------|------------------|-----------------------|------------------|----------------|
| [[system-design\|System Design]] | {from role page} | **{from role page}** | {from role page} | {≤15 words, evidence + what is unvalidated} |
| [[ownership\|Ownership]] | ... | ... | ... | ... |
| [[strategy\|Strategy]] | ... | ... | ... | ... |
| [[domain-expertise\|Domain Expertise]] | ... | ... | ... | ... |
| [[communication\|Communication]] | ... | ... | ... | ... |
| [[decision-making\|Decision Making]] | ... | ... | ... | ... |

Pull level text from the role pages — do not invent it. "Current signal" cells stay short; put reasoning in prose, not in the table.

### Leveling Decision Questions (answer after the round)

4-5 questions **specific to this candidate**, each a binary that maps to floor / target / stretch. Pattern:
1. Did they {do the thing the central probe tests}, or {the failure mode the concern predicts}?
2. Did they **set** {named platform}'s direction and drive its adoption, or **execute** a direction handed to them?
3. Is {their biggest scope claim} evidence of **{stretch}-shaped** or **{target}-shaped** ownership?
4. {Build-vs-buy / context-fit question grounded in the team's real stack}
5. Is {their strongest asset} **production-hardened** or an impressive exploration?

## Recommendation

**{Action} — anchor the round on {the central probe}.**

One paragraph: why this candidate matters (strongest asset, prior scores), the 1-2 questions that decide floor vs target vs stretch, what the round must contain, then **conditional outcomes**: "If {X} *and* {Y}, a {Stretch} conversation is warranted; if {failure mode}, land at {Target} (or {Floor}) and route {Z} to {later step}."

**Never predict the outcome** ("expected Strong Yes") — prior scores inform the load, they do not pre-decide it.

## Related

- [[source-{slug}|Candidate Profile]] — Full source materials
- [[interviews-{product}|{Product} Hiring]] — Team hiring
- [[role-{track}-{target}|{Target} {Title}]] — Target level
- [[role-{track}-{stretch}|{Stretch} {Title}]] — Stretch level
- [[{step}-questions-{slug}|{Step} Interview Guide]] — Tailored questions
```

### 6. Create Interview Questions Guide

Write `wiki/projects/product-{product}/_interviews_/candidate-{slug}/2-{step}-questions-{slug}.md`:

```markdown
---
Category: projects
Tags: [hiring, {step}, candidate, {slug}, {product}, {level}, interview-guide]
Source links:
  - [[1-candidate-{slug}]]
  - [[source-{slug}]]
  - [[interview-rubric-{step}]]
  - [[step-hire-{n}-{step}]]
Created: {date}
Last Updated: {date}
---

# {Step} Guide: {Full Name}

Tailored {step} question bank for [[1-candidate-{slug}|{Full Name}]] ({Level} {Title} candidate, {Product}).

## Calibration Framing

### {Target} Expectations — What "Yes at {Target}" requires (and where {Stretch} begins)

| Dimension | [[role-{track}-{floor}\|{Floor}]] baseline | **[[role-{track}-{target}\|{Target}]] must show** | [[role-{track}-{stretch}\|{Stretch}]] stretch |
|-----------|------------------|-----------------------|------------------|
| [[system-design\|System Design]] | ... | **...** | ... |
{4-5 rows, same text as the candidate page leveling table}

### Risk Profile (from prior rounds)

**Confirmed strengths:**
- {Prior score + interviewer, with the concrete behavior observed}
...

**Open concerns to probe:**
- **{Central concern}** — {verbatim quote}. **The single most important signal to resolve this round.**
- {Other concern} — {one line}
...

> **Interviewer note.** {The specific way this candidate could pass the round without being tested — e.g. "résumé so aligned the failure mode is a comfortable retrospective". Tell the interviewer how to force them onto new ground and demand numbers, not nouns.}

{For system-design: insert the "Primary Challenge" section here — see System Design Preparation below.}

## Question Bank (Tailored to Resume)

### A. {Category} — {Focus}

*Focus: {one line — what this category decides for this candidate}*

1. **"{Question as you would say it aloud to the candidate}"**
   - *Listening for:* {concrete content of a good answer — nouns, mechanisms, numbers}
   - *{Target} signal:* {the behavior that separates {Target} from {Floor}; tie to a resume claim or concern where possible}

2. **"{Question}"**
   - *Listening for:* ...
   - *{Target} signal:* ...

...

### B. {Category} — {Focus} — **CRITICAL FOCUS**

{Mark the 1-2 categories that carry the central probe with **CRITICAL FOCUS**.}

...

{5-7 categories, 3-5 questions each. Number questions **continuously Q1…Qn across all categories** (not A1, B1) so the flow, red-flag and signal tables can cite them.}

## Recommended Interview Flow ({duration} min)

| Time | Section | Top Picks | Purpose |
|------|---------|-----------|---------|
| 0–5 min | Warmup / {…} | Q1, Q2 | {Purpose} |
| 5–15 min | {Category} | Q{n}, Q{n} | {Purpose — **bold the critical sections**} |
...

*Pick {N} in the flow; Q{x}, Q{y}, … are backups by theme.*

{Use cumulative time ranges; the last range must end exactly at {duration}. Allocate the most minutes to the CRITICAL FOCUS categories.}

## Red Flags to Watch For

| Question | Red Flag | What It Indicates |
|----------|----------|-------------------|
| Q{n} / Q{m} | {Observable pattern} | {Which concern it confirms — bold the central one} |
...

## Positive Signals to Confirm "Strong Yes" (and open the {Stretch} conversation)

- {Observable behavior, ideally "unprompted"} ({which concern it rebuts})
...
- {Behavior that signals {Stretch}} → **{Stretch} signal**

## Decision Framework

| Recommendation | Threshold | When to Apply |
|----------------|-----------|---------------|
| **Strong Yes ({Target}; open {Stretch})** | 4.0+ | {Concrete, candidate-specific criteria} |
| **Yes ({Target})** | 3.5–3.9 | {Criteria} |
| **Yes (down-level {Floor})** | 3.0–3.4 | {Criteria — usually "central concern persists / interviewer-steered"} |
| **No** | <3.0 | {Criteria} |

## Scoring Reminder

Score against [[interview-rubric-{step}|the {Step} rubric]]. If a rubric fork exists, say so, name the instrument to use and its weights. Close with one bolded line: **{Target} key differentiator for {First Name}:** {what they have clearly shown already} — the round decides {the 1-2 open questions}.

## Related

- [[1-candidate-{slug}|Candidate Evaluation: {Full Name}]]
- [[source-{slug}|Source: {Full Name} Profile]]
- [[interviews-{product}|{Product} Hiring]]
- [[step-hire-{n}-{step}|{Step} Interview Step]]
- [[interview-rubric-{step}|{Step} Rubric]]
- [[{step}-question-bank|{Step} Question Bank]] (if it exists)
- [[role-{track}-{target}|{Target} {Title}]] · [[role-{track}-{stretch}|{Stretch} {Title}]]
```

### 7. Create Source Page

Write `wiki/sources/source-{slug}.md`:

```markdown
---
Category: sources
Tags: [candidate, resume, {level}, {product}, hiring]
Created: {date}
Last Updated: {date}
---

# Source: {Full Name} Profile

**Source:** {Folder path} (Resume, Briefing, Previous Feedback, etc.)
**Date ingested:** {date}
**Type:** candidate profile

## Summary

{1-2 sentence overview}

## Candidate Overview

| Field | Value |
|-------|-------|
| **Name** | {Full Name} |
| **Current Role** | {Title} @ {Company} |
| **Location** | {Location} |
| **Target Role** | {Title} |
| **Target Level** | {Level} ({Description}) |

## Full Experience

{Complete experience extracted from resume with all details}

## Education

{All education details}

## Technical Skills

{Complete skills list}

## Raw Extracts

### From Resume
{Key quotes/details}

### From Briefing
{Role context, success metrics}

### From Previous Feedback
{Summary of prior round scores and notes}

## Related

- [[1-candidate-{slug}|Candidate Evaluation]]
- [[2-{step}-questions-{slug}|Interview Guide]]
```

### 8. Update Product Page

Find `wiki/projects/product-{product}/product-{product}.md` and add/update Candidate Pipeline table:

```markdown
## Candidate Pipeline

| Candidate | Role | Status | Score |
|-----------|------|--------|-------|
| [[1-candidate-{slug}\|{Full Name}]] | {Title} ({Level}) | **Pre-Interview** | — |
```

### 9. Update Portal

Find `wiki/portal.md` and add under `#### Candidate Evaluations` → `##### product-{product}`:

```markdown
- [[1-candidate-{slug}|{Full Name}]] — {Level} candidate, {Brief background} — **Pre-Interview**
  - [[2-{step}-questions-{slug}|{Step} Guide]] — Tailored questions
```

### 10. Update Log

Append to `wiki/log.md`:

```markdown
## [{date}] ingest | Candidate {Name} (pre-interview)

Processed candidate materials for {Name} ({Role}, {Level}).

**Phase:** pre-interview
**Step:** {Step}
**Product:** {Product}

**Created:**
- [[1-candidate-{slug}|Candidate Evaluation]]
- [[2-{step}-questions-{slug}|{Step} Interview Guide]]
- [[source-{slug}|Source Profile]]

**Updated:**
- product-{product}.md — Candidate Pipeline table
- portal.md — Candidate Evaluations section
```

### 11. Report Results

```
Created: wiki/projects/product-{product}/_interviews_/candidate-{slug}/
├── 1-candidate-{slug}.md
└── 2-{step}-questions-{slug}.md

Source: wiki/sources/source-{slug}.md

Candidate: {Full Name}
Role: {Title} ({Level})
Product: {Product}
Interview Step: {Step}

5 Buckets: {Strong count} Strong, {Probe count} Probe, {Gap count} Gap
{If leveling}: {Level} vs {Level + 1} comparison included

Questions: {N} tailored questions across {M} categories

Ready for {Step} interview.
```

### 12. Stage Changes

Call `/change-management-1-stage` to stage all changes:

```
/change-management-1-stage
  trigger: {user's original instruction}
  operation: pre-interview
  subject: {Candidate Name}
  input_files: {all raw files in candidate folder}
  created_files: {all pages created}
  updated_files: {product page, portal.md, log.md}
```

Do not commit unless user explicitly asks.

## Engineering Screen Preparation (Step 1b)

When `{step}` is `engineering-screen`, the question guide is built differently from the other steps. Read [[step-hire-1b-engineering-screen|Step 1b]] and [[interview-rubric-engineering-screen|Engineering Screen Rubric]] before writing.

**What changes:**

| Aspect | Other steps | Engineering Screen |
|--------|-------------|--------------------|
| Question mode | Hypothetical / live problem | **Retrospective** — dig into systems the candidate actually shipped |
| Source of questions | Rubric criteria | **The candidate's own resume claims**, one deep dive per claim |
| Second deliverable | — | **Gap-routing list** — each gap named and assigned to a downstream stage |
| Roadmap | Not referenced | Guide must name **the live roadmap problems** their experience maps onto |

**Assessment areas to cover** (from [[source-hiring-stage-engineering-screen|the stage brief]]) — build one question category per area:

1. Strategic Thinking & Problem Solving
2. Leadership & Influence
3. Technical Depth
4. Communication & Executive Presence
5. Growth & Ownership Mindset
6. Motivation & Alignment
7. AI Mindset

**Question-guide structure for this step** (replaces the generic 5-7 categories):

- **Background & Motivation** — why now, why this domain
- **Deep Dive: Mechanism** — pick 2-4 shipped systems from the resume; ask *how it actually worked*, not what it did
- **Deep Dive: Scale & Impact** — force numbers (rows, QPS, teams onboarded, cost delta)
- **Deep Dive: Where It Broke** — the failure they own; the limit they hit
- **Strategic Framing & Executive Presence** — can they pitch the system to a non-engineer in two sentences
- **Roadmap Mapping & Build-vs-Buy** — put a real open problem in front of them
- **AI Mindset** — do not ask a canned tooling question; **mine it from the deep dives** (where did they reach for a model because conventional analysis failed)
- **Candidate Questions (Scored)** — what they ask reveals what they think matters

**Interview shape:** ~45 min — 5 background / 25 deep dives / 10 roadmap mapping / 5 candidate questions.

**Red flag to pre-load:** depth that evaporates one layer below the architecture diagram. Every deep dive needs a "and how did that work underneath?" follow-up prepared.

> **Caveat:** this stage is **PRELIMINARY** — weights and scale bounds unconfirmed. Do not present its scores as calibrated.

## System Design Preparation (Step 3)

When `{step}` is `system-design`, the guide is built around **one live design problem**, not a set of résumé retrospectives. Retrospective deep dives belong to `engineering-screen`; mixing them in here is the most common failure.

**Add this section between Risk Profile and Question Bank:**

```markdown
## Primary Challenge: {Problem Name} ({key constraint, e.g. customer-facing, multi-region})

**Rationale:** {Why this problem: it sits at the intersection of the candidate's **greatest strength** ({asset}) and **flagged gap** ({concern}). Quote the JD/mission line it comes from.}

### Problem Statement

> "{The problem exactly as the interviewer will read it aloud — a concrete user, a concrete example query/action, and 2-3 numbered hard requirements (scale, latency/SLA, correctness, compliance). End with 'Walk me through your design.'}"

### Why this challenge
- **Directly relevant:** {which résumé system is the building block — and what's different now}
- **Ambiguity ({Target}):** {which requirements are left open to test requirements-gathering}
- **Hits the flagged gap:** {how it forces the central concern}
- **Correctness/stakes:** {what domain stakes force a hard trade-off}
- **{Floor} vs {Target} vs {Stretch} differentiator:** {Floor} describes …; {Target} owns …; {Stretch} frames …
```

**Question categories follow the phases of that one problem** (adapt names to the domain):

| # | Category | Purpose |
|---|----------|---------|
| A | Requirements Gathering — scope, SLA, correctness bar | Do they box the problem to numbers, or start building what they already know? |
| B | High-Level Architecture | Components with justified trade-offs |
| C | {Domain-critical surface, e.g. AI/NL2SQL, payments ledger} — **CRITICAL FOCUS** if it carries a concern | Production-grade vs prototype |
| D | Distributed Systems / Multi-Region / Consistency — **CRITICAL FOCUS** if it carries a concern | The flagged gap |
| E | Scale, Performance & Cost | "Load grows 20× — what breaks first?" |
| F | Reliability & Correctness | Failure → detection → degradation |
| G | Technical Direction, Build-vs-Buy & Altitude — **{Target}/{Stretch} differentiator** | Direction set vs executed; context-fit build-vs-buy; mentoring; one deliberate push-back question |

**Rules:**
- Every question is **about the primary challenge**. Use the résumé only as a *bridge*: "You built {X} at {Company} — what transfers here, and what doesn't?" Maximum ~3 bridge questions; at most **one** pure retrospective (the direction/adoption story in G).
- The Interviewer note must warn against the comfortable retrospective and demand numbers (SLA, QPS, regions, staleness budget) over architecture nouns.
- Include one **push-back** question ("I'll push back: skip {safeguard}, ship now — convince me otherwise or agree").
- Flow: ~60 min, time ranges summing exactly to 60; pick ~15 questions, list the rest as backups.

## Quality Checklist (run before writing each file)

Fix any "no" before saving:

- [ ] Background quote is **verbatim** from the resume; interpretation lives outside the quote.
- [ ] Every claim is traceable to the source files (no inferred skills, no invented numbers).
- [ ] Leveling uses **floor / target / stretch**, target = recruiter-suggested level; tags carry the target only.
- [ ] Exactly **one** concern is marked as the central/highest-priority probe, with a verbatim quote of its source.
- [ ] Concerns this round can't resolve are routed to a named later step.
- [ ] Other candidates are referenced by **wikilink**, never bare names.
- [ ] Quoted questions contain **no internal names or notes** (recruiter, interviewer, other candidates, "your file says") — they are spoken to the candidate.
- [ ] Each question has *Listening for:* **and** *{Target} signal:*.
- [ ] Questions numbered Q1…Qn continuously; flow/red-flag/signal tables cite Q numbers.
- [ ] Flow time ranges end exactly at the round duration; backups listed.
- [ ] Recommendation gives **conditional outcomes**, never a predicted verdict.
- [ ] Table cells ≤ ~25 words — reasoning goes in prose below the table.
- [ ] (system-design) One Primary Challenge; categories follow its phases; ≤1 pure retrospective.

## Conventions

- **Slug format:** Lowercase, hyphenated name (e.g., `fred-t`)
- **File numbering:** `1-` for candidate page, `2-` for questions guide
- **Step names in files:** `engineering-screen`, `coding`, `system-design`, `hiring-manager` or `team-match`, `bar-raiser`
- **Leveling:** Always floor / target / stretch (target−1 / target / target+1)
- **Questions:** 25-35 tailored questions across 5-7 categories
- **Evidence tables:** Always include specific examples from source materials
- **Pre-assessment:** Mark each bucket as Strong/Probe/Gap with priority
- **Red flags/signals:** 5-8 specific, observable patterns, each citing Q numbers
- **Tone:** decisive and prioritized — bold the one thing that matters most in each section; concise over exhaustive

## Edge Cases

**Missing briefing:** Focus on resume; ask user for role context.

**No product specified:** Ask user — needed for output location.

**Prior feedback exists:** Extract scores, concerns, strengths; build on them.

**Level range given (e.g. JD says P3–P4):** Target = recruiter-suggested level if any, else the upper bound; still bracket floor/stretch.

**Synthesis doesn't exist:** Offer to create role-specific interview guide first.
