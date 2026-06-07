---
name: interview-eval
description: >
  Main interview evaluation workflow. Routes to preparation (pre-interview) or
  post-review (post-interview) sub-skills. Use when the user says "evaluate candidate",
  "interview {name}", "bar raiser for {name}", or works with candidate materials.
allowed-tools: Bash Read Glob AskUserQuestion Skill
---

# Interview Evaluation

Orchestrate candidate evaluation through the interview pipeline by routing to the appropriate sub-skill.

## Input

Raw materials in: `raw/People/Candidates/{Candidate Name}/`

Typical files:
- Resume (PDF)
- Interview briefing (Export)
- LinkedIn profile
- Recruiting intake form
- Interview transcript (closed captions or notes)

## Workflow

### 1. Identify Candidate

List available folders in `raw/People/Candidates/` if not specified:

```bash
ls -1 raw/People/Candidates/
```

**Question:** "Which candidate folder should I process?"

### 2. Determine Phase

**Question:** "What phase is this evaluation?"

| Phase | Description | Sub-Skill |
|-------|-------------|-----------|
| `pre-interview` | Prepare for upcoming interview | `/interview-1-preparation` |
| `post-interview` | Process completed interview | `/interview-2-post-review` |

### 3. Route to Sub-Skill

Based on the phase, invoke the appropriate skill:

**Pre-Interview:**
> Invoke `/interview-1-preparation {candidate-name}`

**Post-Interview:**
> Invoke `/interview-2-post-review {candidate-name}`

## Quick Reference

| User Says | Route To |
|-----------|----------|
| "prepare for interview with {name}" | `/interview-1-preparation` |
| "pre-interview {name}" | `/interview-1-preparation` |
| "evaluate {name} post-interview" | `/interview-2-post-review` |
| "bar raiser for {name}" | `/interview-2-post-review` |
| "complete evaluation for {name}" | `/interview-2-post-review` |

## Example

**User:** evaluate candidate Fred T

**Assistant:** Found `raw/People/Candidates/Fred T/` with:
- Resume (PDF)
- Interview briefing
- LinkedIn profile

What phase is this evaluation?
- `pre-interview` — Prepare for upcoming interview
- `post-interview` — Process completed interview

**User:** pre-interview

**Assistant:** Routing to `/interview-1-preparation Fred T`...
