---
name: interview-2-post-review
description: >
  Post-interview evaluation skill. Creates structured evaluation page with scores,
  evidence, and recommendation. All evaluation aspects are documented — unevaluated
  areas marked as "Not evaluated". Use when the user says "post-interview {name}",
  "bar raiser for {name}", "complete evaluation", or has interview transcript.
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

Optional files:
- Existing source page: `wiki/sources/source-{candidate-slug}.md`
- Resume, briefing (if source page doesn't exist)

## Workflow

### 1. Gather Context

**Question 1: Interview Step**
> "Which interview step was completed?"

Options: `bar-raiser`, `technical`, `system-design`, `hiring-manager`, `culture`

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
- Team project: `wiki/projects/{team-project}/`

### 4. Create Evaluation Page

Write `wiki/projects/{team-project}/candidate-{slug}/candidate-{slug}-my-review.md`

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
**Created:** candidate-{slug}-my-review.md
**Updated:** source-{slug}.md
**Verdict:** {Verdict} ({X.X}/5)
```

### 8. Report Results

```
Created:
- wiki/sources/source-{slug}.md (updated)
- wiki/projects/{team}/candidate-{slug}/candidate-{slug}-my-review.md

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

Call `/capture-changes-git` to stage all changes and create the change log entry:

```
/capture-changes-git
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
