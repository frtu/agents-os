---
name: retrospective-2-questions
description: >
  Pre-meeting retrospective step 2. Reads the prep file from retrospective-1-gather and
  writes the facilitation guide into it: recommended board format, time-boxed agenda,
  and proposed questions numbered 1…N grouped by theme (carry-over first, then each
  provisional theme, then decide and close), each tailored to the team's own items with
  what to listen for. Use when the user says "retro questions", "facilitation guide",
  "prepare the retro agenda", or after /retrospective-1-gather. Does not gather input
  (step 1) or write the report (step 3).
allowed-tools: Bash Read Edit Glob Grep AskUserQuestion Skill
---

# Retrospective — 2. Questions (pre-meeting)

Turn the dossier into a facilitation guide: the questions that get from *what the team already said* to *causes and owned actions* within the time available. A good guide is **tailored** — every question names the team's own item — and **ordered** so the meeting closes the loop first and decides last.

## Files

- `references/question-bank.md` — generic questions by theme and question type. Read it, then **tailor** — never paste generic wording.
- `retrospective-3-report/references/templates/retro-formats.md` — board formats and how their columns map to the report. Read from there (owned by `retrospective-3-report`; both skills must be linked) when choosing the format.

## Parameters

`team`, `date`, `{Retro Folder}` (same resolution as the router: `folder=` → `RETROSPECTIVE_FOLDER` → `wiki/projects/_retrospective_`), `duration` in minutes (default 60).

Input and output: `{Retro Folder}/{date}-{team}-retrospective.md`. If it's missing or `status:` isn't `gathered` or `questions-ready`, stop and route to `/retrospective-1-gather`.

## Process

### 1. Read the dossier

Take from the prep file: the carry-over table (§1), signals (§2), team-raised problems (§3), wins (§4), open questions (§5), provisional themes (§6), gaps (§7).

### 2. Choose the format

Recommend one board format from `retro-formats.md`, with a one-line reason, based on the dossier:

| Dossier shape | Suggested format |
|---|---|
| Many risks / forward-looking worries, a big goal ahead | Sailboat |
| Clear problems, team wants to change practices | Start / Stop / Continue |
| Low morale or tired team | 4Ls or WRAP (appreciations first) |
| Retro called to evaluate a pilot or decide something | Goal-framed |
| Team bored of the usual format | anything they haven't used in the last 3 retros |

Most gathering is already done in step 1, so the board round in the meeting is short: **validate and add**, not start from zero.

### 3. Build the agenda

Time-box to `duration` (60-min default shown; scale proportionally):

| Time | Block | Questions |
|---|---|---|
| 5 | Set the stage | Q1–Q2 |
| 10 | Carry-over — close the loop | Q3–Q… |
| 10 | Validate & add to the gathered board (dot-vote themes) | — |
| 20 | Themes — causes (top 2–3 voted themes) | … |
| 10 | Decide — max 3 High actions, owner, date, signal | … |
| 5 | Close | … |

### 4. Write the questions

Number **continuously 1…N across all themes** (don't restart per theme). Order:

0. **Set the stage** — 1–2 questions.
1. **Carry-over** — one question per previous action that needs discussion (skip items whose evidence is conclusive; list them as "confirm only"), plus open risks and decisions.
2. **One block per provisional theme** (§6), strongest evidence first — 3–5 questions each, running open → impact → cause. Each block opens with a one-line **Context** that cites the dossier items it covers.
3. **Wins to protect** and **Risks ahead** — 2–3 questions each, only if not covered by a theme.
4. **Decide** — the action-shaping questions (three things, owner, date, signal, investigate vs fix, explicitly not doing).
5. **Close.**

Each question:

```markdown
**7. "Your survey says CDC crashes woke on-call four times — which of those could anyone have acted on?"** ★
- *Probes:* §3 item 2 · §2 after-hours pages
- *Listen for:* actionable vs noise; a named root cause vs "it's flaky"
- ↳ follow-up: "What would have to be true for that page not to fire?"
```

- ★ marks the **must-ask** questions that fit in `duration`; aim for ~12–15 ★ in 60 minutes, 20–35 questions total.
- Open questions from §5 must each appear as a question or a decide item.
- Gaps from §7 that the meeting can fill become questions ("What's our current p95?"); others stay as pre-meeting asks.

### 5. Write the guide into the prep file

Replace the `## Facilitation guide` placeholder:

```markdown
## Facilitation guide

**Format:** {format} — {why} · **Duration:** {n} min · **Voting:** {n} dots per person

### Agenda
{table}

### Confirm only (evidence already conclusive)
- {carry-over item} — {evidence}

### Questions

#### 0. Set the stage
**1. …**

#### 1. Carry-over
**3. …**

#### 2. {Theme name} — {pattern}
*Context:* {dossier items}
**7. …**

…

#### {n}. Decide
#### {n+1}. Close

### Facilitator notes
- {sensitivities, e.g. anonymise round on morale; a decision needing someone outside the team}
```

Set frontmatter `status: questions-ready` and update `Last Updated`.

### 6. Log, report, stage

Append to `wiki/log.md`: `## [{today}] retro-prep | {Team} retro {date} (questions)` with format, question count, ★ count, themes.

Report: format + reason, agenda, N questions / ★ count across M themes. Then:

> Run the meeting. Afterwards drop notes, board export or transcripts into `{Raw Retro Folder}` and run `/retrospective-3-report team={team} date={date}`.

Stage with `/change-management-1-stage` (operation `retro-questions`). Never commit unless asked.

## Rules

- **Tailored or cut.** A question that could be asked of any team is either rewritten to name this team's item or dropped.
- **Carry-over first, decisions last.** Never plan a retro that runs out of time before actions.
- **Questions, not answers.** Don't pre-write causes or actions; leading questions become "listen for" notes instead.
- **Blameless phrasing.** Ask about systems, load and decisions — never "who broke…".
