---
name: retrospective-3-report
description: >
  Post-meeting retrospective step 3. Captures everything from the meeting — notes, board
  export in any format (Start/Stop/Continue, Sailboat, WRAP, 4Ls, went-well/improve),
  transcripts, 1:1 or interview notes — plus the prep file from steps 1–2 into a
  decision-ready final report from the template: headline, carry-over status, wins,
  pain points with root cause, risks, and a few owned, dated action items, with a
  carry-over list for the next retro. Also reviews an existing retro report against the
  same bar. Use when the user says "write up the retro", "capture retro notes",
  "retrospective report", "review this retro", or shares a retrospective document.
allowed-tools: Bash Read Glob Grep Edit Write AskUserQuestion Skill
---

# Retrospective — 3. Report (post-meeting)

Turn the meeting into a short record that changes what the team does next cycle. A retro is judged by its **action items** — few, owned, dated, measurable — not by how many sticky notes it captured.

## Files

- `references/templates/retrospective-report.md` — the report template: structure, per-section insight, style, questions to answer, one-minute self-review. **Read it before producing or reviewing.**
- `references/templates/retro-formats.md` — how each board format maps onto the template's sections, plus format-independent rules (votes, risks, wishes → pains). Read it when the board isn't already in Went well / Needs improvement / Start-Stop-Continue form. (Also read by `retrospective-2-questions`.)
- `references/cases/README.md` — registry of synthetic worked examples, indexed by board format and failure pattern. Load **one** matching case when the input's format or shape is unfamiliar — never all.

## Parameters

`team`, `date`, `mode` (`produce` default, or `review`), `{Retro Folder}` (`folder=` → env `RETROSPECTIVE_FOLDER` → `wiki/projects/_retrospective_`), `{Raw Retro Folder}` (`raw=` → `raw/Retrospectives/{Team}/`).

- Prep file (input, from steps 1–2): `{Retro Folder}/{date}-{team}-retrospective.md`
- Report (output): `{Retro Folder}/{date}-{team}-retrospective-report.md`

## Determine the mode

- **Produce** — meeting output exists and the report should be written. → *Produce process*.
- **Review** — the user shares an existing report (or the report file already exists) and wants feedback. → *Review process*.

If unclear, ask one question, then proceed.

## Produce process

### 1. Collect the inputs

- **Prep file** (if it exists): carry-over table, team-raised problems, open questions, themes, and the facilitation guide's numbered questions. No prep file → run standalone: look for the previous `*-{team}-retrospective-report.md` in `{Retro Folder}` for §3 carry-over, and say in the report that no prep was done.
- **Meeting output** in `{Raw Retro Folder}`, pasted, or pointed to: meeting notes, board export or screenshots, dot votes, transcript, **1:1 / interview notes** taken before or after the meeting. Read images too.
- Voice-memo or caption transcripts that are messy → offer `/lint-transcript-normalise` first.

### 2. Capture before curating

Build a working capture (in memory, or in the appendix):

- **Per numbered question** from the guide: what was said, decisions, disagreements. Mark questions **not reached**.
- **Carry-over statuses** confirmed in the meeting (Done / In progress / Dropped / Not started + one-line outcome).
- **Board items** mapped by format (`retro-formats.md`), with votes.
- **Interview / 1:1 notes**: problems, causes and ideas not said in the room. Keep them **anonymous** and mark their source type (`1:1`) so the report can weigh them.

Keep every item the team raised; nothing is dropped silently.

### 3. Write the report from the template

Cluster into 2–4 themes (reuse the prep file's provisional themes; rename or merge if the meeting changed them), then fill the template section by section: Metadata → Summary → Previous actions → Went well → Needs improvement → Risks to watch → Start/Stop/Continue → Action items → Carry-over for next retro → Appendix.

- **Summary:** headline first, with its number; if the retro was called for a decision, answer it here.
- **Previous actions:** from the prep file's §1 with statuses confirmed in the meeting. A pain that recurs behind a "done" action → say the action missed the cause.
- **Needs improvement:** symptom → impact → cause (known / suspected / unknown).
- **Action items:** merge duplicates, move roadmap work out, rewrite actions that restate the problem, cap High at ~3, owner + Due + Success signal; top-voted items reach the table or are parked explicitly.
- **Carry-over for next retro:** what `/retrospective-1-gather` must check next time.
- **Appendix:** link the prep file and raw files; list the guide questions not reached.
- **Never fabricate** owners, dates, numbers or causes. `[need input]`, listed at the end.

Run the template's **one-minute self-review** and fix what fails.

### 4. Write, link, log, stage

1. Write `{Retro Folder}/{date}-{team}-retrospective-report.md` (frontmatter: `Category: projects`, `Tags: [retrospective, {team}]`, `team`, `date`, `cycle`, `prep: "[[{date}-{team}-retrospective]]"`, `previous`, `Source links`, `Created`, `Last Updated`).
2. In the prep file: set `status: reported` and `report: "[[{date}-{team}-retrospective-report]]"`.
3. Append to `wiki/log.md`: `## [{today}] retro-report | {Team} retro {date}` with headline, n actions (n High), gaps.
4. Report to the user: path, headline, action table, `[need input]` list.
5. Stage with `/change-management-1-stage` (operation `retro-report`). Never commit unless asked. Raw files in `raw/` are never modified.

## Review process

1. **Diagnose** in 2–3 lines: team, cycle, and the headline as written.
2. **Check against the template** — each section's *Questions to answer* and the style rules. Highest-impact first:
   - Unowned or `TBD` actions; priority inflation; no due date or success signal.
   - Headline numbers inconsistent or over-scoped (non-prod claimed as prod, range vs point).
   - Contradictions between Went well and Needs improvement.
   - Start/Stop/Continue copied verbatim into actions; roadmap work posing as actions.
   - Symptoms without cause; wins without evidence.
   - Missing follow-up on previous actions; "done" actions whose pain recurs; dropped actions the retro raises again.
   - Retro goal / decision left unanswered; top-voted items with no action.
   - Actions that restate the problem ("try to…", "find better ways…"); luck counted as a win.
   - If a prep file exists: team-raised problems or open questions from the dossier that the report silently dropped.
3. **Deliver:**

   ```markdown
   ## Bottom line
   [Is this retro ready to close? The single biggest fix.]

   ## Findings
   [Numbered, highest impact first. Each: quote/point to the spot → the issue → the fix.]

   ## Keep
   [What the report does well — brief.]

   ## Proposed action table
   [The cut-down, owned version — only if asked or it's the main fix. Owners stay `[need input]` if unknown.]
   ```
4. Comment and advise; rewrite only if asked.

## Rules

- **Generic template, synthetic cases.** Real team history lives in `{Retro Folder}` in the vault, never in `references/`. Cases are anonymised worked examples: systems named by category, people by role, no company-internal names or links.
- **A recurring finding across several retros** → promote it to a generic rule in the template.
- **Blameless.** Describe systems and processes, not people. Interview input stays anonymous.
- **Faithful to the team.** Curate and group, but don't change what the team meant; keep the raw input traceable.
- Hand-offs: executive framing of the outcome → `review-engineering-director`; word-level cleanup → `rewrite-clarity`.
