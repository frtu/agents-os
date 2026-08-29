---
name: interview-2-capture-interview-q-a
description: >
  Capture an interview from a transcript or AI-generated summary into two linked notes:
  a faithful Q&A note and a condensed interview report. Both are generated from the
  templates in references/. Use when the user says "create interview notes",
  "capture interview Q&A", "turn transcript into Q&A", or "write the interview report".
allowed-tools: Bash Read Write Edit Glob AskUserQuestion
---

# Interview Capture: Q&A Note + Report

Transform an interview transcript or AI-generated summary into **two linked notes**, both driven by the templates in `references/`:

| Output | Prefix | Template | Purpose |
|--------|:------:|----------|---------|
| **Q&A Note** | `3a` | [`references/template-interview-q-a.md`](references/template-interview-q-a.md) | Faithful, themed capture — question-by-question, preserves hedges and corrections |
| **Interview Report** | `3b` | [`references/template-interview-report.md`](references/template-interview-report.md) | Condensed synthesis — Pros/Cons + themed prose, light judgment, no scores |

The Q&A note is the *fidelity* layer; the report is the *gist* layer. Both feed the later post-interview evaluation (`/interview-3-post-review`) but neither scores or makes the hire call.

## Source-to-output routing

| Source in candidate folder | Detection Pattern | Best-fit output(s) |
|----------------------------|-------------------|--------------------|
| **Raw transcript** | `*transcript*.md`, `*Interview*.md` (not "Interview Briefing") | Both — `3a` from the transcript, `3b` synthesized from `3a` |
| **Voice memo transcript** | `raw/transcripts/*.md` | Both |
| **AI Q&A summary** (themed questions + answers) | `3a` primarily; `3b` if a report-style summary is also present |
| **AI report** (Pros/Cons, Summary, Motivation, AI Mindset sections) | `*AI recruiting*.md`, `*report*.md` | `3b` primarily |
| **Screenshot / image** | `*.png`, `*.jpg` | Whichever the image contains |

A raw transcript can produce **both** notes: extract the Q&A note first (`3a`), then distill the report (`3b`) from it. A pre-condensed AI export usually maps to one — a Q&A-style summary → `3a`, a Pros/Cons report → `3b`. When in doubt, produce both; a thin report is still useful.

## Workflow

### 1. Read the templates

Always start by reading both templates so the output matches the current house structure (they may have been revised):

```bash
cat "references/template-interview-q-a.md"
cat "references/template-interview-report.md"
```

Follow the template's own frontmatter, section order, and "How to fill it correctly" rules. Do **not** inline a format here — the templates are the single source of truth.

### 2. Identify source & context

Find interview source material in the candidate folder:

```bash
ls -1 "{Raw Candidate Materials}/" 2>/dev/null | \
  grep -iE "(transcript|interview|summary|report|notes)" | \
  grep -viE "^Interview Briefing"
```

Resolve the placeholders both templates need: `{product}`, `{slug}`, `{level}`, `{step}`, `{Interviewer}`, `{Date}`, `{Source}`. Pull `{product}`/`{level}` from the pre-interview candidate page (`1-candidate-{slug}.md`) if it exists; ask the user only for genuinely ambiguous values (e.g., interview step).

If both an image and text source exist, read the image first (`Read` tool) — it often holds hand-written notes not in the transcript.

### 3. Extract and capture

**For the Q&A Note (`3a`):**
- Group questions by **theme**, not chronology (Intro & Motivation, Technical Deep-Dive, Impact & Achievements, Behavioral & Ownership, Candidate's Questions).
- Quote each question verbatim (or close). Capture answers as **atomic bullets** close to what was said.
- **Preserve corrections, hedges, and "I don't know"s** — these are signal; never smooth them away.
- Nest follow-ups under their parent with `↳`.
- Add the optional `**In short:**` one-line prose synthesis where bullets need a gist, and a one-glyph `*Signal:*` tag (`✅ / ⚠️ / ❌ / ➖`).

**For the Interview Report (`3b`):**
- Lead Technical Abilities with **Pros before Cons**; keep both concrete (name the mechanism, the trade-off, the specific wobble).
- Write **Summary**, **Critical Decision Making**, **Motivation**, and **AI Mindset** as short themed paragraphs — synthesis, not transcript.
- If a dimension wasn't discussed (e.g., AI tool usage), **say so explicitly** rather than omitting it.
- Light judgment is allowed; **no scores or verdict** — those belong in the evaluation.

### 4. Write both output files

Write to the candidate folder:

- `wiki/projects/product-{product}/_interviews_/candidate-{slug}/3a-{step}-qa-{slug}.md`
- `wiki/projects/product-{product}/_interviews_/candidate-{slug}/3b-{step}-report-{slug}.md`

Use the exact frontmatter and body structure from each template. Cross-link the two: the report's Related section points to `3a` ("the faithful capture this summarizes"); the Q&A note's Related section points to `3b`. Both link the pre-interview candidate page and the source profile. Leave any link plain text if the target page doesn't exist yet (wiki-schema Rule 22).

If the source only supports one note, create that one and note in the report why the other was skipped (e.g., "No verbatim Q&A available — report generated from AI summary only").

### 5. Update dossier links

- **Candidate page** (`1-candidate-{slug}.md`) — add `3a` and `3b` to the Interview Steps line.
- **portal.md** — under the candidate's entry, add the two capture notes.
- **log.md** — append a capture entry (see below).

### 6. Update log

Append to `wiki/log.md`:

```markdown
## [{date}] capture | Candidate {Name} (interview capture)

Captured {Step} interview for {Name} into Q&A note + report.

**Phase:** post-interview (capture)
**Step:** {Step}
**Source:** {Transcript / AI report}
**Created:**
- 3a-{step}-qa-{slug}.md
- 3b-{step}-report-{slug}.md
**Updated:** 1-candidate-{slug}.md, portal.md
```

### 7. Report results

```
Created:
- wiki/projects/product-{product}/_interviews_/candidate-{slug}/3a-{step}-qa-{slug}.md
- wiki/projects/product-{product}/_interviews_/candidate-{slug}/3b-{step}-report-{slug}.md

Candidate: {Name}
Step: {Step} · Interviewer: {Name} · Source: {Source}

Q&A Note (3a): {N} questions across {M} themes
Report (3b): {P} pros / {C} cons · sections: Summary, Decision Making, Motivation, AI Mindset

Next: /interview-3-post-review {candidate-name} to score these into an evaluation
```

### 8. Stage changes

Call `/change-management-1-stage` to stage all changes and create the change log entry:

```
/change-management-1-stage
  trigger: {user's original instruction}
  operation: interview-capture
  subject: {Candidate Name}
  input_files: {transcript / AI report used}
  created_files: 3a-{step}-qa-{slug}.md, 3b-{step}-report-{slug}.md
  updated_files: 1-candidate-{slug}.md, portal.md, log.md
```

Do not commit unless the user explicitly asks.

## Conventions

- **Templates are the source of truth.** Read `references/template-interview-*.md` each run and follow their structure and fill-rules; don't reinvent the format.
- **File naming:** `3a-{step}-qa-{slug}.md` (Q&A note) and `3b-{step}-report-{slug}.md` (report). `{step}` ∈ `coding`, `system-design`, `hiring-manager`, `team-match`, `bar-raiser`.
- **Slug format:** lowercase, hyphenated name (e.g., `fred-t`).
- **Neutral capture over judgment.** The Q&A note records; the report synthesizes with light judgment. Neither scores — the verdict lives in `/interview-3-post-review`.
- **Corrections are gold.** Preserve hedges, self-corrections, and "I don't know"s in both notes.
- **One pair per interview step.** A candidate with three rounds gets three `3a/3b` pairs, each linked from the candidate page.

## Edge Cases

**Only an AI report available (no transcript):** produce `3b` from it; create a thin `3a` only if the report contains attributable questions, otherwise skip `3a` and note the reason in `3b`.

**Only a Q&A summary available (no report-style sections):** produce `3a`; synthesize `3b` from `3a` (Pros/Cons and Summary can be distilled from the themed answers).

**Screenshot with partial text:** extract what's visible, mark unclear spans `[unclear]`, and note the limitation in the note header's Source line.

**No clear questions in transcript:** in `3a`, use `### Q: "{topic}"` from topic shifts; in `3b`, rely on the Summary and Pros/Cons which don't require verbatim questions.

**Multiple interviewers:** note the interviewer per question in `3a`; the report `3b` stays single-voice with interviewers named in the header.

## Integration

Called from `/interview-eval` when interview sources are detected, or standalone:

```
/interview-2-capture-interview-q-a {candidate-name}
/interview-2-capture-interview-q-a {source-file-path}
```
