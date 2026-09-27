---
name: retrospective
description: >
  Router for the team retrospective workflow. Picks the team and retro date, detects
  the phase from the files already in the retrospective folder, and routes to
  retrospective-1-gather (pre-meeting: gather team problems + last retro's carry-over),
  retrospective-2-questions (pre-meeting: numbered facilitation questions by theme) or
  retrospective-3-report (post-meeting: notes, board, interviews → final report; or
  review an existing report). Use when the user says "retro", "retrospective for {team}",
  "prepare the retro", "run the retro workflow", or works with retro material and the
  phase is unclear.
allowed-tools: Bash Read Glob Grep AskUserQuestion Skill
---

# Retrospective (Router)

Orchestrates a team retrospective from preparation to final report. The router only selects the team and date, detects the phase, and hands off; the rules live in the sub-skills.

| Phase | Skill | When | Produces |
|---|---|---|---|
| 1 — Gather (pre-meeting) | `retrospective-1-gather` | Before the meeting | `{Retro Folder}/{date}-{team}-retrospective.md` — carry-over from last retro, team-raised problems, signals, open questions, provisional themes |
| 2 — Questions (pre-meeting) | `retrospective-2-questions` | After gather, before the meeting | `## Facilitation guide` in the same file — format, agenda, questions numbered 1…N by theme |
| 3 — Report (post-meeting) | `retrospective-3-report` | After the meeting | `{Retro Folder}/{date}-{team}-retrospective-report.md` — final report from the template, with carry-over for the next retro. Also reviews an existing report |

## Configuration

`{Retro Folder}` — where retro files live, relative to the vault root. Resolved in this order (all sub-skills use the same rule):

1. **Parameter** `folder=<path>` on the invocation.
2. **Env var** `RETROSPECTIVE_FOLDER`.
3. **Default** `wiki/projects/_retrospective_`.

`{Raw Retro Folder}` — where raw input for one retro is dropped (survey exports, board exports, meeting notes, interview transcripts): parameter `raw=<path>`, else `raw/Retrospectives/{Team}/`. Pasted text and explicit file paths are always accepted too.

`{team}` is a lowercase hyphenated slug (`checkout-squad`); `{date}` is the **meeting date** `YYYY-MM-DD`.

## Workflow

### 1. Select or create the team

```bash
ls -1 "{Retro Folder}" 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}-.+-retrospective(-report)?\.md$' \
  | sed -E 's/^[0-9-]{11}(.+)-retrospective(-report)?\.md$/\1/' | sort -u
```

Ask the user to pick an existing team or name a new one (→ slug). Show each team's latest retro date.

### 2. Select the meeting date

Default: the next meeting date the user gives, or today. If a `{date}-{team}-retrospective.md` already exists for an upcoming date, offer it first.

### 3. Detect the phase

Each step sets `status:` in the prep file's frontmatter: `gathered` (step 1) → `questions-ready` (step 2) → `reported` (step 3).

```bash
P="{Retro Folder}/{date}-{team}-retrospective.md"
[ -f "$P" ] && grep -m1 '^status:' "$P" || echo "status: none"
ls -1t "{Raw Retro Folder}" 2>/dev/null | head
```

| Found for `{date}-{team}` | Phase | Route to |
|---|---|---|
| No prep file (`status: none`) | Pre-meeting, not started | `retrospective-1-gather` |
| `status: gathered` | Pre-meeting, input gathered | `retrospective-2-questions` |
| `status: questions-ready` + meeting notes / board export / transcript in `{Raw Retro Folder}` or pasted | Post-meeting | `retrospective-3-report` (produce) |
| `status: reported` | Done | `retrospective-3-report` (review or update) |
| User shares a retro report from elsewhere | — | `retrospective-3-report` mode=review |

If detection is ambiguous (e.g. prep done but no notes yet), state what was found and ask: *"Prep and questions are ready. Is the meeting done — capture notes into the report?"*

New files in `{Raw Retro Folder}` since the prep file was written usually mean meeting output → phase 3.

### 4. Route

Invoke the sub-skill with the resolved parameters:

```
/retrospective-1-gather    team={team} date={date} [folder=…] [raw=…]
/retrospective-2-questions team={team} date={date} [folder=…] [duration=60]
/retrospective-3-report    team={team} date={date} [folder=…] [raw=…] [mode=produce|review]
```

The phases can run back-to-back (1 → 2 in one sitting is normal). Stop after phase 2: the meeting happens between 2 and 3.

## Quick reference

| User says | Route to |
|---|---|
| "prepare the retro for {team}", "gather retro input" | `retrospective-1-gather` |
| "what did we commit to last retro?" | `retrospective-1-gather` (carry-over only) |
| "retro questions", "facilitation guide", "agenda for the retro" | `retrospective-2-questions` |
| "write up the retro", "capture retro notes", "retro report" | `retrospective-3-report` |
| "review this retro" + a document | `retrospective-3-report` mode=review |
