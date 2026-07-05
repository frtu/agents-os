---
name: weekly-2-consolidate
description: >
  Phase 2 of the weekly digest. Consolidate the per-product wiki weekly pages
  (produced by weekly-1-aggregate) into a single Slack-ready final report written
  for a wider audience, with honest completion status. Use when the user says
  "consolidate weekly", "weekly phase 2", "weekly final report", or when invoked by
  the weekly-digest router.
allowed-tools: Bash Read Write Edit Glob AskUserQuestion
references:
  - references/weekly-report-template.md
---

# Weekly Digest — Phase 2: Consolidate

Produce a single Slack-ready file combining ALL products, rewritten so people
**outside the delivering team** get a clear, trustworthy picture of what shipped.

This phase does **not** read raw contributor updates. Its inputs are the artifacts
created by `weekly-1-aggregate`.

The Phase-1 wiki pages are a faithful, exhaustive log. Phase 2 is **not** a
reformat of that log — it is an **editorial pass** that denoises, deduplicates, and
reprioritizes it down to what a wider audience should read. **Cutting is the job.**
A good consolidated report is markedly shorter than the sum of its inputs. If your
draft is nearly as long as the per-product pages, you have not done Phase 2.

## Inputs

- **Per-product wiki files** (from Phase 1):
  - `wiki/projects/_weekly_/<date>-product-a.md`
  - `wiki/projects/_weekly_/<date>-product-b.md`

  Read every `## Key Projects`, `## Highlights / Lowlights`, and `## Eng Excellence`
  section. Emoji are already normalized to `[:emoji:]` text; `:checked:` markers
  denote projects completed this week. Each project line already carries a
  `[[project-x|Display Name]]` wiki link — **keep it** (see drill-down links below).
- **Portal:** `wiki/portal.md` — for each project's **Alias** (display name),
  **Target** date, and **priority marker** (`(Px)` embedded in the
  description). Priority is for **ordering only** — never print it in the report.
- **Judgment context** (read to rank and phrase, not to copy):
  - `wiki/projects/product-search/product-search.md` — the **L1/L2/L3
    prioritization framework**. Use it to decide which projects deserve space.
  - The touched **project pages** (`wiki/projects/.../project-*.md`) — pull the
    one-line objective (Synopsis/Overview) and audience/stakeholder from here to
    phrase **why the work matters**, instead of guessing. Do not read every page —
    only consult one when a project's "why" is unclear from its wiki lines.

If the per-product wiki files for `<date>` don't exist, **STOP** and tell the user
to run `/weekly-1-aggregate <date>` first.

## Output

- `wiki/projects/_weekly_/<date>-consolidated.md` — the Slack-ready final report.

---

# The Workflow

## 1. Gather

1. Read both `<date>-product-*.md` files.
2. Read `wiki/portal.md`; build a lookup of alias, target date, priority, and the
   `[[project-x|...]]` link key per project.
3. Collect, per product: the project list (with health circle, tasks, `:checked:`,
   and its `[[...]]` link), the highlights, and the Eng Excellence / BAU items.

## 2. File name

`wiki/projects/_weekly_/<date>-consolidated.md` with content following the **`references/weekly-report-template.md`** structure. The `<date>` is the same as the input wiki files.

## 3. Denoise & consolidate (do this BEFORE formatting)

This is the heart of Phase 2, together with wider-audience rewriting (§4). The
Phase-1 pages over-report on purpose; here you cut to signal. Apply these filters
**hard** — the human-edited final reports are consistently ~40-60% shorter than the
generated draft, mostly because these cuts were not applied aggressively enough.

**A. Merge micro-updates into one specific line.** A project with 4-7 task bullets
that are all facets of the same effort should become **1-3 lines**, each naming a
concrete outcome. Do not list every commit-sized step.

**B. Drop pure mechanics.** Cut lines whose only content is internal plumbing with
no audience meaning: version bumps (`SDK sync to v3.11.0`), image/publish fixes,
dependency enrichment, DAG wiring, classloader fixes, bean resolution. These belong
in the Phase-1 log, not the report. Keep only the outcome that a stakeholder cares
about.

**C. Cap the volume.** Target **≤ 3 task lines or max 5 per project** and **≤ 8 project
lines total** across the report. If a project's *only* activity this week is a
single low-signal mechanical item, **drop the project entirely** rather than
surface a thin line. Flagship / P1 / `:checked:` projects always survive.

| Phase-1 wiki (many micro-lines) | Consolidated (one specific line) |
|---|---|
| `[:done:] Auto sunset snapshot reload pipeline — edge cases fixed` · `[:done:] SDK sync to v3.11.0` · `[:done:] Decimal/float precision fix` · `[:done:] Docker image publishing fix` | `[:done:] Auto-sunset snapshot reload at watermarks (resource saving)` + `[:done:] Decimal/float precision fix` — SDK/Docker plumbing dropped |
| 8 separate BAU support bullets | 2-3 bullets, related items combined with `;` |

**D. Reprioritize.** Order by importance, not by input order (ordering rules live in
the template reference). A single high-impact line outranks five mechanical
`[:done:]` lines.

## 4. Wider-audience expression & honest status

The per-product wiki lines are written for the team; rewrite each **survivor** of
the §3 cut so a non-team reader understands **what** the work is and **why it
matters**, and so the status honestly reflects what actually shipped.

**A. Rewrite each surviving task line for a wider audience**

- **Lead with a verb** describing the effort: `Developing…`, `Assisting…`,
  `Preparing…`, `Evaluated…`, `Enforcing…`. Avoid bare noun fragments.
- **Add the audience or benefit ("why")** when it isn't self-evident: who it's for
  or what it unlocks (e.g. `… for Copilot`, `… allowing Ops to search the business
  field`). When the "why" isn't obvious from the wiki line, pull it from the project
  page's objective/audience (see Inputs → Judgment context).
- **Strip internal jargon**: field names, repo names, tool/library names, version
  bumps, source tags like `(Wiki)`, and undefined acronyms. Keep the outcome, drop
  the mechanics.

**B. Assign status honestly**

`[:done:]` is reserved for **shipped, complete outcomes**. PoCs, drafts "polished",
designs "validated", and intermediate progress are `[:work_in_progress:]`, not done.
When phrasing tempts you into a completed-noun claim, recast it as an ongoing-effort
verb. When in doubt, downgrade to `[:work_in_progress:]`.

Also keep **target dates honest** — prefer a tighter, truthful target (`End of July`, `Mid Q3`) over a vague optimistic one (`Q3`).

**C. Highlights — admit strictly, default to N/A**

A highlight qualifies **only** if it has **end-user impact** (a customer, domain
team, or partner is materially affected) **OR** a **significant release**
(production cutover, GA, major migration complete, deprecation closed). A qualifying
highlight can usually **name the team or customer who benefits**; if it can't, it
probably doesn't qualify.

**Never** promote these to a highlight — they are internal wins, not audience news:

- Internal reviews, design "validated", PoC built or demoed => Design in progress
- Refactoring new SDK/framework, tracing/observability upgrades => Internal improvement
- Onboarding a feature internally, internal alignment reached => Preparing for external review

It is normal for a week to have **no** qualifying highlight — write `- N/A` rather
than promoting an internal win. Then reword survivors to **audience + benefit**,
strip internal names, and prefer `:tada-animated:`. Aim for **0-3 highlights total**.

**D. Eng Excellence — plain text, combined, denoised**

- Follow template rules.

## 5. Fill the template

Pour the denoised, rewritten survivors into the output structure defined in
**`references/weekly-report-template.md`**. Read that file and follow its fill
instructions exactly — it owns the header format, section order, health/status
emoji, drill-down `[[project|Display]]` links, priority-stripping, product ordering,
emphasis (`**bold**` / `~~strikethrough~~`), and Eng Excellence formatting.

## 6. In case of doubt

- If a surviving line is unclear, consult the project page for its objective and
  audience (see Inputs → Judgment context).
- Still unclear, ask the project lead or team for clarification.
- After clarification, propose to enrich project page.

## 7. Write the consolidated file (iterative)

A. Write the final consolidated report to `wiki/projects/_weekly_/<date>-consolidated.md`, submit to git and **STOP**. 
B. Ask the user to review it & ask for feedbacks. Apply user comments and loop to step A.
C. If all good, proceed to post-phase bookkeeping.

---

## Post-Phase Bookkeeping

After the consolidated file is confirmed:

### Update log

Append to `wiki/log.md`:

```markdown
## [<date>] ingest | Weekly consolidated <date>

Consolidated Product A + Product B weekly pages into a Slack-ready report.

**Created:** <date>-consolidated.md
**Highlights:** <count or N/A>
**Projects surfaced:** <list>
```

### Final report to user

```
Phase 2 (consolidate) complete. Created:
- wiki/projects/_weekly_/<date>-consolidated.md

Source wiki pages:
- <date>-product-a.md, <date>-product-b.md
```

---

## Conventions Summary

- **Input is the per-product wiki files**, not raw updates. Run Phase 1 first.
- **Editorial pass, not reformat:** denoise, dedupe, reprioritize. The report is
  markedly shorter than its inputs — cutting is the job.
- **Denoise budget:** ≤ 3 task lines 5 max per project, ≤ 8 projects total; merge
  micro-updates into one specific outcome line; drop pure mechanics (version bumps,
  image/publish fixes, DAG/plumbing); drop projects whose only update is thin.
- **Drill-down links:** KEEP the `[[project-x|Display Name]]` link on each project
  line so reviewers can click through. Display label = clean alias.
- **Keep `[:emoji:]` text** for task status — Slack renders them.
- **Priority markers are ordering-only** — never print `(P1)`/`(P2)`.
- **Product order:** Product A first, then Product B. Never interlace. Within a
  product: P1 → completed → flagship → smaller.
- **Wider-audience expression:** verb-led lines that state audience/benefit; pull
  the "why" from project-page objective/audience when unclear; strip internal jargon.
- **Honest status:** `[:done:]` only for shipped, complete outcomes; PoCs/drafts/
  "validated" designs stay `[:work_in_progress:]`; keep target dates truthful.
- **Highlight admission:** end-user impact OR significant release only, and it should
  name who benefits; RFCs/PoCs/re-platforming never qualify; `- N/A` when none do.
- **Formulation:** bold the key term; `~~strikethrough~~` deprecated systems.
- **Eng Excellence:** plain text, 2-3 combined bullets, one BAU %.
- **`:checked:`** after a project name when marked Complete in the wiki files.

## Edge Cases

- **Only one product this week:** header names just that team; skip the missing product's block.
- **No highlights qualify:** write `- N/A` under **Highlights / Lowlights** (common — not a failure).
- **BAU range (e.g. "10-15%") in wiki file:** pick the midpoint for the consolidated file.
- **Missing target date in portal.md:** omit `:date:` for that project rather than inventing one.
- **Project with only a mechanical/plumbing update:** drop it from the report rather than surface a thin line.
