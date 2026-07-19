---
name: interview-2-capture-interview-q-a
description: >
  Generate structured interview Q&A notes from transcripts or AI-generated summaries.
  Creates formatted notes with concise bullet points and natural prose for each
  question-answer pair. Use when the user says "create interview notes", 
  "format interview Q&A", or "turn transcript into Q&A".
allowed-tools: Bash Read Write Edit Glob AskUserQuestion
---

# Interview Q&A Notes

Transform interview transcripts or AI-generated summaries into structured Q&A notes with dual-layer formatting: concise bullet points for quick scanning plus natural prose for context.

## Input Sources

| Source Type               | Detection Pattern                   | Example                                          |
| ------------------------- | ----------------------------------- | ------------------------------------------------ |
| **Raw transcript**        | `*transcript*.md`, `*Interview*.md` | `2026-07-19 Interview-Fred-T.md`                 |
| **Voice memo transcript** | `raw/transcripts/*.md`              | `raw/transcripts/2026-07-19 Interview-Fred-T.md` |
| **Screenshot/image**      | `*.png`, `*.jpg`                    | `Interview Notes.png`                            |
| **AI summary export**     | `*AI*.md`, `*summary*.md`           | `Interview Summary - Candidate.md`               |

## Output Format

Each Q&A block follows this structure:

```markdown
### {Question}

**Key Points:**
- {Concise bullet point 1}
- {Concise bullet point 2}
- {Concise bullet point 3}

{Natural prose paragraph expanding on the answer with context, examples, and nuance. 
This should read like a well-written summary that captures the candidate's actual words 
and reasoning, not just extracted facts.}
```

### Format Guidelines

| Element        | Guidelines                                                                         |
| -------------- | ---------------------------------------------------------------------------------- |
| **Question**   | Use `###` header, verbatim or lightly cleaned from source                          |
| **Key Points** | 2-5 bullet points, each ≤15 words, factual extraction                              |
| **Prose**      | 2-4 sentences, captures tone and reasoning, uses candidate's words where impactful |

## Workflow

### 1. Identify Source

Check the candidate folder for interview source material:

```bash
ls -1 "{Raw Candidate Materials}/" 2>/dev/null | \
  grep -iE "(transcript|interview|summary|notes)" | \
  grep -viE "^Interview Briefing"
```

**Priority order:**
1. Screenshot/image IF EXIST (needs reading)
2. Raw transcript (needs Q&A extraction)

### 2. Extract Q&A Pairs

**From screenshot/image:** (IF EXIST)
- Read image content using Read tool
- Extract visible Q&A pairs
- Structure same as markdown format

**From raw transcript:**
- Identify interviewer questions (usually preceded by interviewer speaking)
- Extract candidate responses
- Group related exchanges into logical Q&A blocks

### 3. Generate Dual-Layer Notes

For each Q&A pair:

1. **Extract key points** — Distill into 2-5 bullet points
   - Focus on facts, decisions, metrics, names
   - Keep each bullet ≤15 words
   - Use active voice

2. **Write natural prose** — Expand with context
   - Capture candidate's reasoning and tone
   - Include specific examples they mentioned
   - Preserve impactful direct quotes
   - Connect to role requirements where relevant

### 4. Organize by Theme

Group Q&A blocks into logical sections:

| Section                        | Content                                           |
| ------------------------------ | ------------------------------------------------- |
| **Background & Motivation**    | Self-intro, career history, why this role         |
| **Technical Deep Dive**        | Architecture, system design, technical decisions  |
| **Problem Solving**            | Complex cases, debugging, trade-offs              |
| **Leadership & Collaboration** | Team dynamics, conflict resolution, communication |
| **Q&A / Candidate Questions**  | Questions the candidate asked                     |

### 5. Write Output File

Write to: `wiki/projects/{team-project}/_interviews_/candidate-{slug}/{N}b-interview-q-a.md`

Use this frontmatter:

```markdown
---
Category: projects
Tags: [hiring, candidate, interview-notes, {step}, {level}, {domain}]
Source links:
  - [[source-{candidate-slug}]]
Created: {date}
Last Updated: {date}
---

# Interview Q&A: {Candidate Name}

**Source:** {AI summary / Voice memo transcript / Raw transcript}
**Interview Step:** {Step name}
**Interviewer:** {Name}
**Date:** {Date}

---

{Q&A sections organized by theme}
```

## Example Output

```markdown
---
Category: projects
Tags: [hiring, candidate, interview-notes, {step}, {level}-{level+1}, {product-domain}]
Source links:
  - [[source-fred-t]]
Created: 2026-07-19
Last Updated: 2026-07-19
---

# Interview Q&A: Fred T

**Source:** Generated summary
**Interview Step:** {step}
**Interviewer:** {interviewer name}
**Date:** 2026-07-19

---

## Background & Motivation

### Can you introduce yourself?

**Key Points:**
- Bullet A
- Bullet B

Prose paragraph summarizing the candidate's introduction, career history, and motivations for applying to the role. Include any relevant context or examples they provided.

### Why are you leaving XX?

**Key Points:**
- Bullet C
- Bullet D

Prose paragraph summarizing the candidate's reasons for leaving their current position, including any challenges or opportunities they are seeking in the new role.

---

## Technical Deep Dive

### What is XX technology? How would you explain it to a non-technical person?

**Key Points:**
- Bullet E
- Bullet F

Prose paragraph summarizing the candidate's explanation of a deep technical concept, including any analogies or examples they used to illustrate the concept.
```

## Conventions

- **Slug format:** Lowercase, hyphenated name (e.g., `fred-t`)
- **File naming:** `{N}b-interview-q-a.md` where N matches the interview step number
- **Key Points:** Always use `**Key Points:**` heading for consistency
- **Prose length:** 2-4 sentences per Q&A block
- **Direct quotes:** Use sparingly, only when candidate's exact words are impactful

## Edge Cases

**No clear questions in transcript:**
- Identify topic shifts and create logical section headers
- Use `### {Topic}` format instead of verbatim questions

**Very long answers:**
- Split into multiple Q&A blocks if distinct topics
- Focus key points on most important elements
- Prose should summarize, not transcribe

**Screenshot with partial text:**
- Extract what's visible
- Mark unclear sections with `[unclear]`
- Note limitations in file header

**Multiple interviewers:**
- Note interviewer for each question if identifiable
- Group by interviewer if format makes sense

## Integration

This skill can be called from `/interview-eval` when interview sources are detected:

```
/interview-2-capture-interview-q-a {candidate-name}
```

Or standalone when user provides a specific source file:

```
/interview-2-capture-interview-q-a {source-file-path}
```
