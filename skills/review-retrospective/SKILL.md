---
name: review-retrospective
description: Produce or review a team retrospective report. Turns raw retro input (board export in any format — Start/Stop/Continue, Sailboat, WRAP, 4Ls, went-well/improve — sticky notes, meeting notes, Wiki page) into a decision-ready report — headline, wins, pain points with root cause, Start/Stop/Continue, and a short list of owned, dated action items — or critiques an existing retro report against the same bar. Applies to any team; team-specific context lives in a case registry. Use when the user says "write up the retro", "retrospective report", "review this retro", "clean up retro notes", or shares a retrospective document.
allowed-tools: Bash Read Glob Grep Edit Write
---

# Retrospective Report

Turn a retro session into a short record that changes what the team does next cycle. A retro is judged by its **action items** — few, owned, dated, measurable — not by how many sticky notes it captured.

## Files

- `references/templates/retrospective-report.md` — the generic template: structure, per-section insight, style, and questions to answer. **Read it before producing or reviewing.**
- `references/templates/retro-formats.md` — how each board format (Sailboat, WRAP, 4Ls, goal-framed, …) maps onto the template's sections, plus format-independent rules (votes, risks, wishes → pains). Read it when the input isn't already in Went well / Needs improvement / Start-Stop-Continue form.
- `references/cases/README.md` — registry of cases (team → file, with its board format and the failure pattern it illustrates). Each case holds a team's sub-areas, recurring themes, key metrics, and past retros with raw input, review findings, a proposed action table, and carry-over actions. All shipped cases are synthetic worked examples.

## Determine the mode

- **Produce mode** — the user supplies raw retro input and wants the report written. → *Produce process*.
- **Review mode** — the user shares an existing retro report and wants feedback. → *Review process*.

If unclear, ask one question, then proceed.

## Step 0 — Identify the team

1. Identify the team from the input (title, page, user's words). If you can't, ask.
2. Read `references/cases/README.md`. If the team has a case file, **load only that file**: use its team context (grouping, themes, metrics) and its last retro's **Carry-over** list for §3 (previous action items).
3. If the team is new, proceed with the generic template and offer to create a case file at the end. If the input's **format or failure pattern** matches a case in the registry, load that **one** case as a worked example (how it maps, reviews, produces) — not for its team context.

## Produce process

1. **Read the raw input fully.** Keep every item the team raised; nothing is dropped silently.
2. **Map the format.** If the board isn't in the template's shape, map each column per `retro-formats.md`: recover the pain behind wishes/learned items, route risks to *Risks to watch*, refile misfiled stickies, and use votes as priority.
3. **Cluster into themes** (2–4). Name the pattern (e.g. "manual toil", "cost") before placing items.
4. **Fill the template** section by section (Metadata → Summary → Previous actions → Went well → Needs improvement → Risks to watch (if any) → Start/Stop/Continue → Action items).
   - Summary: headline first, with its number, then wins / pain points / direction. If the retro was called to answer a question (evaluate a pilot, close a project), answer it here.
   - Needs improvement: symptom → impact → cause; mark cause as known / suspected / unknown.
   - Action items: merge duplicates, move ongoing roadmap work out, rewrite actions that restate the problem, cap High at ~3, add Due and Success signal; top-voted items reach the table or are parked explicitly.
5. **Never fabricate** owners, dates, numbers, or root causes. Mark gaps `[need input]` and list them at the end.
6. Run the template's **one-minute self-review** and fix what fails.
7. Save where the user asks. If the source is in a vault `raw/` folder, don't overwrite it — write alongside or to `output/`.

## Review process

1. **Diagnose** in 2–3 lines: team, cycle, and the headline as written.
2. **Check against the template** — each section's *Questions to answer* and the style rules. Highest-impact first:
   - Unowned or `TBD` actions; priority inflation; no due date or success signal.
   - Headline numbers inconsistent or over-scoped (non-prod claimed as prod, range vs point).
   - Contradictions between Went well and Needs improvement.
   - Start/Stop/Continue copied verbatim into actions; roadmap work posing as actions.
   - Symptoms without cause; wins without evidence.
   - Missing follow-up on previous action items; "done" actions whose pain recurs; dropped actions the retro raises again.
   - Retro goal / decision left unanswered; top-voted items with no action.
   - Actions that restate the problem ("try to…", "find better ways…"); luck counted as a win.
3. **Deliver:**

   ```markdown
   ## Bottom line
   [Is this retro ready to close? The single biggest fix.]

   ## Findings
   [Numbered, highest impact first. Each: quote/point to the spot → the issue → the fix.]

   ## Keep
   [What the report does well — brief.]

   ## Proposed action table
   [The cut-down, owned version — only if the user asks for it or it's the main fix. Owners stay `[need input]` if unknown.]
   ```
4. Comment and advise; rewrite only if asked.

## After either mode — update the registry

Append the retro to the team's case file (`## Retro YYYY-MM-DD`: captured content, review findings, carry-over) and update `references/cases/README.md`, per its "Adding to the registry" rules. Ask before creating a case for a new team.

## Rules

- **Generic template, specific cases.** Team names, systems, and metrics go in `references/cases/`, never in the template or this file.
- **Blameless.** Describe systems and processes, not people.
- **Faithful to the team.** Curate and group, but don't change what the team meant; keep the raw input traceable.
- For executive-level framing of the retro's outcome, hand off to `review-engineering-director`; for word-level cleanup, `rewrite-clarity`.
