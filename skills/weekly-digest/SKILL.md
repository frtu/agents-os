---
name: weekly-digest
description: >
  Router for the two-phase weekly digest workflow. Runs weekly-1-aggregate then
  weekly-2-consolidate. Use when the user says "digest weekly", "process weekly
  updates", "weekly for {product}", or wants to take team updates all the way from
  raw contributor files to the Slack-ready consolidated report.
allowed-tools: Bash Read Glob AskUserQuestion Skill
---

# Weekly Digest (Router)

Orchestrates the weekly digest end-to-end by chaining two sub-skills:

| Phase           | Skill                  | Produces                                                                           |
| --------------- | ---------------------- | ---------------------------------------------------------------------------------- |
| 1 — Aggregate   | `weekly-1-aggregate`   | Per-product wiki pages (`<date>-product-*.md`) + updated project `## Key Features` |
| 2 — Consolidate | `weekly-2-consolidate` | Slack-ready `<date>-consolidated.md` for a wider audience                          |

This router selects the date and runs the phases in order; the detailed rules live
in the sub-skills.

**Streamlined flow:** The workflow minimizes confirmation prompts. User approval
happens via `git diff` / `git add` after all files are written. Only genuinely
ambiguous decisions (new project creation, conflicting mappings) pause for input.

## Inputs

- **Raw updates:** `raw/daily/Weekly updates/<date>-<product>/` — one `.md` per contributor
- **Portal:** `wiki/portal.md` — valid project list, aliases, and target dates

## Workflow

### 1. Identify the date

If the user gave a date, use it. Otherwise list available folders and ask:

```bash
ls -1d "raw/daily/Weekly updates/"*/ 2>/dev/null | sed 's#.*/\([^/]*\)/#\1#'
```

```
Available weekly updates:
- 2026-07-03
- 2026-06-26
- 2026-06-05

Which date should I process?
```

### 2. Run Phase 1 — Aggregate

> Invoke `/weekly-1-aggregate <date>`

Let it run to completion (it writes the per-product wiki files and updates project
pages, pausing for confirmations along the way).

### 3. Run Phase 2 — Consolidate

Once Phase 1 reports complete and the `<date>-product-*.md` files exist:

> Invoke `/weekly-2-consolidate <date>`

This reads the per-product wiki files and produces the consolidated Slack report.

### 4. Final report

Summarize both phases' outputs:

```
Weekly digest for <date> complete.

Phase 1 (aggregate):
- wiki/projects/_weekly_/<date>-product-a.md
- wiki/projects/_weekly_/<date>-product-b.md
- project pages updated: <list>

Phase 2 (consolidate):
- wiki/projects/_weekly_/<date>-consolidated.md
```

## Running a single phase

- Only need the per-product wiki pages / project tracking? → `/weekly-1-aggregate <date>`
- Wiki pages already exist and you only want the Slack report? → `/weekly-2-consolidate <date>`

## Quick Reference

| User Says                                    | Route To                        |
| -------------------------------------------- | ------------------------------- |
| "digest weekly {date}"                       | full router (Phase 1 → Phase 2) |
| "aggregate weekly" / "weekly phase 1"        | `/weekly-1-aggregate`           |
| "consolidate weekly" / "weekly final report" | `/weekly-2-consolidate`         |
