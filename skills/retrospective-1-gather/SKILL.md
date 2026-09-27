---
name: retrospective-1-gather
description: >
  Pre-meeting retrospective step 1. Gathers what the team already raised (survey,
  async board, 1:1 notes, channel threads, incident list) and the previous retro's
  carry-over (action items, risks, open questions) into one dossier:
  {Retro Folder}/{date}-{team}-retrospective.md. Offers a short async pre-retro survey
  when no team input exists yet. Use when the user says "prepare the retro",
  "gather retro input", "what did we commit to last retro", or runs /retrospective
  before a meeting. Does not write questions (retrospective-2-questions) or the final
  report (retrospective-3-report).
allowed-tools: Bash Read Write Edit Glob Grep AskUserQuestion Skill
---

# Retrospective — 1. Gather (pre-meeting)

Build the facilitator's dossier before the meeting: **what we committed to last time**, **what the team is already saying**, and **what the meeting must answer**. Good output means the meeting opens by closing the loop and spends its time on causes and decisions, not on re-listing problems.

## Files

- `references/template-retro-prep.md` — structure of the prep file, per-section guidance, and the pre-retro survey. **Read it before writing.**

## Parameters

| Parameter | Resolution |
|---|---|
| `team` | slug, from the router or ask |
| `date` | meeting date `YYYY-MM-DD`, from the router or ask |
| `{Retro Folder}` | `folder=` → env `RETROSPECTIVE_FOLDER` → `wiki/projects/_retrospective_` |
| `{Raw Retro Folder}` | `raw=` → `raw/Retrospectives/{Team}/` (plus anything pasted or pointed to) |

Output: `{Retro Folder}/{date}-{team}-retrospective.md`.

## Process

### 1. Find the previous retro

```bash
ls -1 "{Retro Folder}" 2>/dev/null | grep -E -- "-{team}-retrospective(-report)?\.md$" | sort | awk -v d="{date}" '$0 < d' | tail -2
```

- Prefer the latest `*-{team}-retrospective-report.md` before `{date}`. Read its **Action items**, **Risks to watch**, open decisions and **Carry-over for next retro**.
- Only a prep file, no report → the last meeting was never written up. Use its questions and themes, and add "previous retro never reported" to §7.
- Nothing found → *first retro on record*; §1 says so.

### 2. Read the team's raw input

List `{Raw Retro Folder}` and read everything relevant: survey exports, async board exports (any format — see `retrospective-3-report/references/templates/retro-formats.md` for column meanings), 1:1 or interview notes, channel threads, incident/on-call summaries, delivery metrics. Read images too (board screenshots).

**No team input at all?** Offer the pre-retro survey from the template, pre-filled with the carry-over list from step 1. Write the prep file with §1 filled and `status: gathered`, note "awaiting survey" in §7, and **stop** — tell the user to rerun when responses are in.

### 3. Fill the prep file

Create the folder if needed (`mkdir -p "{Retro Folder}"`), then write the file per the template:

1. **Carry-over** — every previous action with owner/due/success signal; look for evidence already available (metric moved, ticket closed) and put it in *Evidence found*. Status stays a question for the meeting unless the evidence is conclusive.
2. **Signals** — only metrics you can source. Compare with the previous retro's numbers where they exist.
3. **Team-raised problems** — every item kept, grouped, counted, quoted close to the team's words, **not attributed**. Flag items that recur from past retros.
4. **Wins raised** — with evidence or `[need input]`.
5. **Open questions** — from last retro (unresolved decisions, puzzles) and new ones raised.
6. **Provisional themes** — 2–5 named patterns, each pointing at its items.
7. **Gaps** — missing numbers, unknown statuses, people not heard from.

Leave `## Facilitation guide` as the `status: pending` placeholder.

### 4. Log, report, stage

Append to `wiki/log.md`:

```markdown
## [{today}] retro-prep | {Team} retro {date} (gather)

**Created:** [[{date}-{team}-retrospective]] · **Previous:** {prev or none}
**Input:** {n} raw files · {x} carry-over actions · {y} team-raised problems · {z} themes
```

Report to the user: file path, carry-over count (with evidence found vs to confirm), themes, top gaps. Then:

> Next: `/retrospective-2-questions team={team} date={date}` to build the facilitation guide.

Stage with `/change-management-1-stage` (operation `retro-gather`, subject `{team} {date}`). Never commit unless asked.

## Rules

- **Never fabricate** owners, statuses, numbers or causes. `[need input]` and list it in §7.
- **Anonymous by default.** Team-raised items carry counts, not names.
- **Blameless.** Systems and processes, not people.
- **Faithful.** Group and quote; don't rewrite what the team meant. Keep raw files untouched in `raw/`.
- **Don't solve in the dossier.** No actions here — causes and actions are for the meeting and step 3.
