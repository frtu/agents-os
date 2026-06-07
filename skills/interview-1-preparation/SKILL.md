---
name: interview-1-preparation
description: >
  Pre-interview preparation skill. Creates candidate source page with profile analysis,
  strengths/concerns assessment, and tailored interview questions. Use when the user
  says "prepare for interview", "pre-interview {name}", or wants to prep before meeting a candidate.
allowed-tools: Bash Read Write Edit Glob Grep AskUserQuestion
---

# Interview Preparation (Pre-Interview)

Create a comprehensive candidate source page with profile analysis and interview preparation materials.

## Input

Raw materials in: `raw/People/Candidates/{Candidate Name}/`

Required files:
- Resume (PDF or Markdown) — Experience, skills, education

Optional files:
- Interview briefing — Role context, team, hiring manager
- LinkedIn profile — Current role, tenure
- Recruiting intake form — Success metrics, challenges

## Workflow

### 1. Gather Context

**Question 1: Role Details**
> "What role and level is this candidate interviewing for?"

Examples:
- "Senior Software Engineer, Product (IC Level 3)"
- "Engineering Lead, Product (Manager Level 1)"

**Question 2: Interview Step**
> "Which interview step are you preparing for?"

Options: `bar-raiser`, `technical`, `system-design`, `hiring-manager`, `culture`, `screening`

**Question 3: Focus Areas (Optional)**
> "Any specific areas you want to probe? Leave blank for standard assessment."

Allow user to specify concerns or areas of interest.

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

### 4. Create Source Page

Write `wiki/sources/source-{candidate-slug}.md`:

```markdown
---
Category: sources
Tags: [candidate, resume, {level}, {domain}, hiring]
Created: {date}
Last Updated: {date}
---

# Source: {Candidate Name} Profile

**Source:** {Candidate Name} folder (Interview Briefing, LinkedIn, Resume, Recruiting Intake Form)
**Date ingested:** {date}
**Type:** candidate profile

## Summary

{1-2 sentence overview: who they are, what role, key background}

## Candidate Overview

| Field | Value |
|-------|-------|
| **Name** | {Name} |
| **Current Role** | {Title} @ {Company} |
| **Location** | {Location} |
| **Target Role** | {Role Title} |
| **Target Level** | {Level} ({Level Description}) |
| **Languages** | {Languages if relevant} |

## Experience Summary

### {Company} ({Dates}) — {Title}

- **{Theme}** — {Accomplishment with metrics}
- **{Theme}** — {Accomplishment}
...

{Repeat for each relevant role}

## Education

- {University} — {Degree} ({Years})

## Strengths Assessment

| Strength | Evidence | Relevance to Role |
|----------|----------|-------------------|
| **{Strength}** | {Specific example from resume} | {Why it matters} |
...

## Potential Concerns

| Concern | Context | Mitigation |
|---------|---------|------------|
| **{Concern}** | {Why it's a concern} | {How to probe in interview} |
...

## Role Context

### Position Details

- **PID:** {if available}
- **Hiring Manager:** {Name}
- **Division:** {Division}
- **Location:** {Location}

### Team Structure

{Who they'd work with, report to, coordinate with}

### Success Metrics (6-12 months)

1. {Metric 1}
2. {Metric 2}
...

### Challenges

1. {Challenge 1}
2. {Challenge 2}
...

## Pre-Interview Assessment Summary

### 5 Buckets Framework

| Bucket | Assessment | Priority |
|--------|------------|----------|
| 1. Problem Solving | {Strong/Probe/Gap} — {reason} | {Low/Medium/High} |
| 2. Leadership & Strategy | {Assessment} | {Priority} |
| 3. Operational Excellence | {Assessment} | {Priority} |
| 4. Culture & Collaboration | {Assessment} | {Priority} |
| 5. Talent & Team Building | {Assessment} | {Priority} |

### Key Interview Questions

**Shine Questions:** (let them demonstrate strengths)
- "{Question about their strongest area}"
- "{Question about quantified accomplishment}"

**Gap Questions:** (probe concerns)
- "{Question about identified gap}"
- "{Question about potential concern}"

**Open Exploration Questions:** (discover unknowns)
- "{Question to uncover working style}"
- "{Question about decision-making approach}"
- "{Question about failure/learning}"

## Related

- [[role-{track}-{level}|{Level} {Title}]] — Target level
- [[hiring-process|Hiring Process]] — Interview pipeline
- [[step-hire-{n}-{step}|{Step Name}]] — Next interview
- [[interview-rubric-{step}|{Step} Rubric]] — Scoring criteria
```

### 5. Update Log

Append to `wiki/log.md`:

```markdown
## [{date}] ingest | Candidate {Name} (pre-interview)

Processed candidate materials for {Name} ({Role}).

**Phase:** pre-interview
**Step:** {Step}
**Created:** source-{slug}.md
```

### 6. Report Results

```
Created: wiki/sources/source-{slug}.md

Candidate: {Name}
Role: {Role} ({Level})
5 Buckets: {Strong count} Strong, {Probe count} Probe, {Gap count} Gap

Shine questions: {N}
Gap questions: {N}
Open exploration questions: {N}

Ready for {Step} interview.
```

### 7. Stage Changes

Call `/capture-changes-git` to stage all changes and create the change log entry:

```
/capture-changes-git
  trigger: {user's original instruction}
  operation: pre-interview
  subject: {Candidate Name}
  input_files: {all raw files in candidate folder}
  created_files: {source page created}
  updated_files: {log.md}
```

Do not commit unless the user explicitly asks.

## Conventions

- **Slug format:** Lowercase, hyphenated name (e.g., `fred-t`)
- **Open questions:** Include 2-3 exploratory questions beyond standard probes
- **Evidence tables:** Always include specific examples from source materials
- **Pre-assessment:** Mark each bucket as Strong/Probe/Gap with priority

## Edge Cases

**Missing briefing:** Focus on resume analysis, ask user for role context.

**No role specified:** Ask user before proceeding — needed for accurate assessment.

**Synthesis doesn't exist:** Offer to create role-specific interview guide first.
