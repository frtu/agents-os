---
name: interview-3-post-review
description: >
  Post-interview evaluation skill. Creates structured evaluation page with scores,
  evidence, and recommendation. All evaluation aspects are documented — unevaluated
  areas marked as "Not evaluated". Use when the user says "post-interview {name}",
  "post interview for {name}", "complete evaluation", or has interview transcript.
allowed-tools: Bash Read Write Edit Glob Grep AskUserQuestion
references:
  - references/evaluation-template.md
---

# Interview Post-Review (Post-Interview)

Create a comprehensive evaluation page with coarse-grained Pros & Cons based on P3/P4 competencies.

## Competency Framework

Use competencies from [[competency-matrix|Competency Matrix]] :

| Category       | Competencies                                                                | Interview Signals                               |
| -------------- | --------------------------------------------------------------------------- | ----------------------------------------------- |
| **Craft**      | Coding, Software Design, System Design, Domain Expertise, Product Expertise | Tech depth, architecture, problem decomposition |
| **Culture**    | Collaboration, Communication, Fit & Growth, Community                       | Clarity, teamwork, passion, learning            |
| **Leadership** | Decision Making, Strategy                                                   | Trade-offs, prioritization, planning            |
| **Talent**     | Hiring, Inspire                                                             | Mentoring, role modeling, team building         |
| **Result**     | Impact, Ownership, Operational Excellence                                   | Delivery, reliability, metrics-driven           |

## Input

Raw materials in: `raw/People/Candidates/{Candidate Name}/`

Required files:
- Interview transcript (closed captions or notes)
- Q&A Note + Report (from `interview-2-capture-interview-q-a`, files prefixed `3a-` and `3b-`)

Optional files:
- Existing source page: `wiki/sources/source-{candidate-slug}.md`
- Resume, briefing (if source page doesn't exist)

## Workflow

### 0. Check for Capture Files

Before starting evaluation, check if the Q&A note and report (skill 2 outputs) exist:

```bash
ls -1 "wiki/projects/product-{product}/_interviews_/candidate-{slug}/" 2>/dev/null | grep -E "^3[ab]-"
```

**If capture files are missing** (no `3a-` or `3b-` files found):
- Prompt: "No Q&A note or report found. Run `/interview-2-capture-interview-q-a {candidate-name}` first to capture the interview, then return here for evaluation."
- Call `/interview-2-capture-interview-q-a {candidate-name}` automatically (or ask user to confirm).
- Wait for skill 2 to complete and return.
- Resume with step 1 below.

**If capture files exist:** proceed directly to step 1.

### 1. Gather Context

**Question 1: Interview Step**
> "Which interview step was completed?"

Options: `engineering-screen`, `technical`, `system-design`, `hiring-manager`, `culture`, `bar-raiser`

| Step option | Wiki step page | Rubric |
|-------------|----------------|--------|
| `engineering-screen` | [[step-hire-1b-engineering-screen\|Step 1b]] *(P5+/M2+ only)* | [[interview-rubric-engineering-screen\|Engineering Screen Rubric]] — **PRELIMINARY** |
| `technical` | [[step-hire-2-coding\|Step 2]] | [[interview-rubric-coding\|Coding Rubric]] |
| `system-design` | [[step-hire-3-system\|Step 3]] | [[interview-rubric-system\|System Rubric]] |
| `hiring-manager` / `culture` | [[step-hire-4-team-match\|Step 4]] | [[hire-4-team-match-template\|Team Match Template]] |
| `bar-raiser` | [[step-hire-5-bar-raiser\|Step 5]] | [[interview-rubric-bar-raiser\|Bar Raiser Rubric]] |

**Question 2: Role Details** (if source page doesn't exist)
> "What role and level?"

**Question 3: Interviewer**
> "Who conducted the interview?"

### 2. Read Materials

| File Type                | What to Extract                                             |
| ------------------------ | ----------------------------------------------------------- |
| **Transcript**           | Questions asked, responses, direct quotes, timestamps       |
| **Source page**          | Pre-interview assessment, strengths, concerns               |
| **Competency reference** | [[competency-matrix\|Competency Matrix]] depending on level |

### 3. Find Related Wiki Pages

- Source page: `wiki/sources/source-{candidate-slug}.md`
- Role definition: `wiki/people/roles/role-ic-{level}.md`
- Team project: `wiki/projects/product-{product}/`

### 4. Create Evaluation Page

Write `wiki/projects/product-{product}/_interviews_/candidate-{slug}/4-{step}-evaluation-{slug}.md`

Use the template from `references/evaluation-template.md`.

**Key principles:**
- **Coarse-grained Pros & Cons** — Max 3-4 items each, competency-based
- **Format:** `**{Competency}** ({X}/5) : {One-line evidence}`
- **Not evaluated** — List aspects not probed with reason
- Pull direct quotes from transcript as evidence

### 5. Score Calculation

Average competency scores by category:

```
Final = (Craft + Culture + Leadership + Result) / 4
```

| Band           | Score Range | Recommendation          |
| -------------- | ----------- | ----------------------- |
| **Strong Yes** | 4.0+        | Exceptional, clear hire |
| **Yes**        | 3.5 - 3.9   | Solid, meets bar        |
| **Lean Yes**   | 3.0 - 3.4   | Meets with gaps         |
| **No**         | < 3.0       | Does not meet bar       |

#### Engineering Screen exception

If `{step}` is `engineering-screen`, do **not** compute the verdict from the five rating fields alone. Use [[interview-rubric-engineering-screen|the rubric]] and apply these three adjustments:

1. **Narrative outranks field scores.** The stage brief defines **7 assessment areas** but the ATS form exposes only **5 rating fields** — Leadership & Influence, Growth & Ownership, Motivation & Alignment, and AI Mindset have nowhere to land. Uniform mid scores next to a narrative documenting exceptional depth means the form ran out of room, not that the candidate was average. Score from the evidence; note the divergence explicitly.
2. **Fit gate is separate from ability.** Real, verified depth that maps onto **no open problem on the live roadmap** is *Do Not Proceed for fit*, not a low ability score. Say which of the two it is.
3. **Produce the gap-routing list.** This stage has a second deliverable besides the verdict: every named gap classified **correctable** vs **fundamental** and assigned to a downstream stage to probe. Add a section to the evaluation page:

```markdown
## Gap Routing

| Gap | Correctable / Fundamental | Route to | What to probe |
|-----|---------------------------|----------|---------------|
| {Gap} | {Classification} | [[step-hire-3-system\|Step 3: System]] | {Specific question} |
```

Every Strength must attach a **landing site** — the roadmap problem it applies to. A strength with no landing site is a fact, not a signal.

> **Caveat:** this rubric is **PRELIMINARY** (n=1 worked example, [[source-engineering-screen-dpe-architect|DPE Architect 2026-05-21]]); weights, scale bounds, and level calibration are proposed, not confirmed. State this in the evaluation page rather than presenting the score as calibrated.

### 6. Update Source Page

Add to the existing source page:

```markdown
## Wiki Pages Created

- [[{synthesis-page}|{Guide Title}]] — Synthesis for interview
- [[{team-project}|{Team Name}]] — Team project overview
- [[candidate-{slug}|Candidate Evaluation: {Name}]] — Post-interview evaluation (**{Verdict}, {X.X}/5**)

## Interview Completed

**Date:** {date}
**Interviewer:** {Name}
**Duration:** ~{N} minutes
**Verdict:** **{Verdict} ({X.X}/5)** — {Next step}

**Key Observations:**
- {Observation 1}
- {Observation 2}
- {Observation 3}
- {Gap or concern}
```

### 7. Update Log

Append to `wiki/log.md`:

```markdown
## [{date}] ingest | Candidate {Name} (post-interview)

Processed candidate materials for {Name} ({Role}).

**Phase:** post-interview
**Step:** {Step}
**Created:** 4-{step}-evaluation-{slug}.md
**Updated:** source-{slug}.md
**Verdict:** {Verdict} ({X.X}/5)
```

### 8. Report Results

```
Created:
- wiki/sources/source-{slug}.md (updated)
- wiki/projects/product-{product}/_interviews_/candidate-{slug}/4-{step}-evaluation-{slug}.md

Candidate: {Name}
Role: {Role} ({Level})
Verdict: {Verdict} ({X.X}/5)

Scores:
- {Criterion 1}: {X.X}/5
- {Criterion 2}: {X.X}/5
- {Criterion 3}: {X.X}/5
- Communication: {X.X}/5

Pros: {count}
Cons: {count}
Not evaluated: {count}
Remaining risks: {count}

Next: Share with hiring manager
```

### 9. Stage Changes

Call `/change-management-1-stage` to stage all changes and create the change log entry:

```
/change-management-1-stage
  trigger: {user's original instruction}
  operation: post-interview
  subject: {Candidate Name}
  input_files: {transcript and other raw files in candidate folder}
  created_files: {evaluation page created}
  updated_files: {source page, log.md}
```

Do not commit unless the user explicitly asks.

## Conventions

- **Slug format:** Lowercase, hyphenated name (e.g., `fred-t`)
- **Quote extraction:** Pull direct quotes from transcript with context
- **Score precision:** Use one decimal (e.g., 4.1/5)
- **Evidence tables:** Always include quote or specific example
- **Not evaluated:** If a planned question wasn't asked, mark section as "Not evaluated"
- **Pre vs Post scores:** Show both to track how assessment changed

## Edge Cases

**No transcript:** Ask user for notes and key observations. Mark transcript-based sections as "Not evaluated — no transcript".

**No source page:** Create minimal source page first, then evaluation.

**Multiple interviews:** Create separate evaluation pages per step, link them together.

**Team project doesn't exist:** Create minimal team project page, then nest candidate folder.
