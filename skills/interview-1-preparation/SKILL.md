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

Options: `coding`, `system-design`, `hiring-manager` or `team-match`, `bar-raiser`

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

> "{1-2 sentence compelling summary from resume}"

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

### {Concern}
{Why it's a concern for the role. How to probe in interview.}

### {Concern}
...

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

{If {Level}-{Level+1} evaluation requested, include leveling section:}

## {Level}-{Level+1} Leveling

### Level Comparison

| Dimension | [[role-ic-{Level}|{Level}]] Signal | [[role-ic-{Level+1}|{Level+1}]] Signal | Evidence |
|-----------|-------------------------------------|----------------------------------------|----------|
| **Scope** | Feature/Team | Domain | {Assessment} |
| **Ownership** | Features end-to-end | Domain technical direction | {Assessment} |
| **Strategy** | Multi-phase projects | Domain roadmaps | {Assessment} |
| **Design** | Components (well-defined) | Ambiguity, cross-boundary | {Assessment} |
| **Domain Expertise** | Team domain | SME for domain | {Assessment} |
| **Influence** | Cross-team | Cross-domain | {Assessment} |

### Leveling Decision Questions

After interview, answer:
1. Did they *define* technical direction, or *execute* someone else's vision?
2. Did they align stakeholders across domains, or within their team?
3. Did they change engineers' career trajectories, or just help on tasks?
4. Can they present to executives, or only technical peers?

## Recommendation

**{Pre-interview recommendation}**

{Brief rationale with suggested focus areas for interview.}

## Related

- [[source-{slug}|Candidate Profile]] — Full source materials
- [[interviews-{product}|{Product} Hiring]] — Team hiring
- [[role-{track}-{level}|{Level} {Title}]] — Target level
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

{If leveling evaluation:}

### {Level} vs {Level+1} — What "Yes at {Level+1}" Requires

| Dimension | {Level} baseline | **{Level+1} must show** |
|-----------|------------------|-------------------------|
| [[software-design|Software Design]] | Components in well-defined scenarios | **Designs in ambiguity, cross-boundary** |
| [[system-design|System Design]] | Contributes to tech strategy | **Owns domain tech strategy** |
| [[domain-expertise|Domain Expertise]] | Team domain | **SME for domain** |
| [[strategy|Strategy]] | Multi-phase projects | **Domain roadmaps, secures buy-in** |
| [[ownership|Ownership]] | Team ownership | **Domain ownership, sets roadmap** |

### Risk Profile (from prior rounds)

**Confirmed strengths:**
- {Strength from prior feedback}
...

**Open concerns to probe:**
- {Concern to address}
...

## Question Bank (Tailored to Resume)

### A. {Category} — {Focus}

{Brief rationale for this category based on candidate's background.}

1. **"{Question tailored to specific resume experience}"**
   - *Listening for:* {What distinguishes good from great answer}

2. **"{Question}"**
   - *Listening for:* {Signals}

...

### B. {Category} — {Focus}

...

{Include 5-7 categories with 3-5 questions each, tailored to:
- Specific resume accomplishments to probe deeper
- Gaps identified in strengths assessment
- Level-distinguishing behaviors
- Role-specific requirements}

## Recommended Interview Flow ({duration} min)

| Time | Section | Top Picks | Purpose |
|------|---------|-----------|---------|
| 5 min | Warmup | Self-intro, Q{n} | Establish tone, motivation |
| 10 min | {Category} | Q{n}, Q{n} | {Purpose} |
...

## Red Flags to Watch For

| Question | Red Flag | What It Indicates |
|----------|----------|-------------------|
| Q{n} | {Pattern} | {Concern} |
...

## Positive Signals to Confirm "Strong Yes"

- {Specific behavior to look for}
...

## Decision Framework

| Recommendation | Threshold | When to Apply |
|----------------|-----------|---------------|
| **Strong Yes** | 4.0+ | {Criteria} |
| **Yes ({Level})** | 3.5-3.9 | {Criteria} |
| **Yes (down-level)** | 3.0-3.4 | {Criteria} |
| **No** | <3.0 | {Criteria} |

## Related

- [[1-candidate-{slug}|Candidate Evaluation: {Full Name}]]
- [[source-{slug}|Source: {Full Name} Profile]]
- [[interviews-{product}|{Product} Hiring]]
- [[step-hire-{n}-{step}|{Step} Interview Step]]
- [[interview-rubric-{step}|{Step} Rubric]]
- [[role-{track}-{lower-level}|{Lower Level} {Title}]]
- [[role-{track}-{upper-level}|{Upper Level} {Title}]]
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

## Conventions

- **Slug format:** Lowercase, hyphenated name (e.g., `fred-t`)
- **File numbering:** `1-` for candidate page, `2-` for questions guide
- **Step names in files:** `coding`, `system-design`, `hiring-manager` or `team-match`, `bar-raiser`
- **Leveling:** Include {Level} vs {Level + 1} comparison when level range requested
- **Questions:** 25-35 tailored questions across 5-7 categories
- **Evidence tables:** Always include specific examples from source materials
- **Pre-assessment:** Mark each bucket as Strong/Probe/Gap with priority
- **Red flags/signals:** 4-6 specific patterns per section

## Edge Cases

**Missing briefing:** Focus on resume; ask user for role context.

**No product specified:** Ask user — needed for output location.

**Prior feedback exists:** Extract scores, concerns, strengths; build on them.

**Level range ({Level}-{Level + 1}):** Include full leveling comparison framework.

**Synthesis doesn't exist:** Offer to create role-specific interview guide first.
