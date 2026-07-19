---
name: weekly-1-aggregate
description: >
  Phase 1 of the weekly digest. Aggregate raw contributor updates (Slack-formatted)
  into per-product wiki weekly pages and roll each project's Key Features checklist
  forward. Use when the user says "aggregate weekly", "weekly phase 1", "weekly for
  {product}", or when invoked by the weekly-digest router. Produces the per-product
  wiki files that weekly-2-consolidate reads.
allowed-tools: Bash Read Write Edit Glob Grep AskUserQuestion
---

# Weekly Digest — Phase 1: Aggregate

A 4-step interactive workflow that processes raw contributor updates into
**per-product** wiki weekly pages and updates the individual project pages:

1. `wiki/projects/_weekly_/<date>-product-a.md` — wiki page for the Product A team
2. `wiki/projects/_weekly_/<date>-product-b.md` — wiki page for the Product B team
3. Updated `## Key Features` checklists on each touched `project-*.md` page

The single consolidated Slack report is produced by the **next phase**,
`weekly-2-consolidate`, which reads the per-product wiki files created here.

The workflow is **interactive** — each step pauses for user confirmation before
moving on. Do not skip ahead; do not guess on ambiguous mappings.

## Inputs

- **Raw updates:** `raw/daily/Weekly updates/<date>-<product>/` — one `.md` per contributor
- **Portal:** `wiki/portal.md` — single source of truth for valid project list.
  Entries are formatted as:

  ```
  [[project-x|Project: X]] — short description — Alias: `Display Name` — Target: <date>
  ```

  The alias is the **display name** used in downstream reports.
  The target date is used in the `:date:` field.
- **Project pages:** `wiki/projects/<product-x>/<area>/project-*.md`.
  Each contains a `## Key Features` markdown checklist (`- [ ]` / `- [x]`)
  that tracks completion across weeks.

## Outputs (handoff to Phase 2)

- `wiki/projects/_weekly_/<date>-product-a.md` and `<date>-product-b.md`
- Updated `## Key Features` on touched project pages
- Portal target dates + `## Sources` links updated
- These per-product wiki files are the **input** to `weekly-2-consolidate`.

## Ambiguity Handling

**STOP and ask** if any of these occur:

1. Task-to-project mapping is unclear (multiple plausible projects)
2. A significant task stream has no matching project in portal.md
3. Contributors report conflicting status for the same work item
4. A contributor's update is missing key sections
5. Project is missing a target date or `## Key Features` section in portal/project page

Never invent project groupings. Never silently guess.

## Emoji Normalization

In raw inputs, contributors use Slack image-style emoji (`![:emoji:](url)`).
Normalize these to plain text form (`:emoji:` / `[:emoji:]`) using the
**`unformat`** skill before parsing — run it over the raw files for the date:

```bash
python3 .claude/commands/unformat/scripts/normalize_slack_emoji.py "raw/daily/Weekly updates/<date>-<product>/"*.md
```

Use `--dry-run` first to preview. See the `unformat` skill for details.

---

# The 4-Step Workflow

Each step ends with a checkpoint. Show the user what you have, get confirmation,
then proceed.

## Step 1 — Project Mapping & Selection

**Goal:** For each product (Product A + Product B), match every task in the raw
contributor updates to a valid project from `portal.md`.

### 1.1 Identify date and products

If the user didn't specify a date, list available folders and ask:

```
Available weekly updates:
- 2026-06-12 (product-a, product-b)
- 2026-06-05 (product-a, product-b)
- 2026-05-29 (product-a, product-b)

Which date should I process? (both products will be digested)
```

### 1.2 Read raw updates

For each `raw/daily/Weekly updates/<date>-<product>/<date> <Name>.md`:

1. Normalize emoji first with the `unformat` skill (see [Emoji Normalization](#emoji-normalization)).
2. Read the file.
3. Extract contributor name from filename.
4. Parse sections: **Highlights / lowlights**, **Key Projects**, **Eng Excellence**.

### 1.3 Load valid projects from portal.md

Read `wiki/portal.md`. Under the `## Projects` section, parse:

- All `[[project-*]]` entries under `### product-a`
- All `[[project-*]]` entries under `### product-b`

For each entry, capture:

- Wiki link (e.g. `project-xx-migration`)
- Title (e.g. `Project: Platform Migration`)
- **Alias / Display Name** (e.g. `YY - Migration`) — from `Alias:` field
- **Target date** (e.g. `Mid Q3`) — from `Target:` field
- Whether it is a child (indented under another) — child projects are preferred
  when a task matches them specifically

### 1.4 Map each task to the closest project

**Rules:**

- Use ONLY existing projects from portal.md. Never invent a new grouping.
- Prefer **child / sub-project** over parent when a task matches it specifically.
  Examples:
  - `Reload from Archive` task → `project-reload-archive` (NOT `project-a-write`)
  - `XX migration to new cluster` → `project-xx-cluster-migration`
- If a task could plausibly map to multiple projects → **STOP and ask the user**:

  ```
  Ambiguous mapping for task: "Component template support for Domain A"
  Candidates:
    a) project-reload-archive
    b) project-user-service
    c) other (specify)
  ```
- If a task has no plausible project match → **candidate it for Eng Excellence**.

### 1.4.1 Eng Excellence default heuristic (Pattern: operational work)

Operational, incident, and one-off tasks default to **Eng Excellence** WITHOUT asking, UNLESS they represent **an improvement on an in-progress feature** of a tracked project (then keep them under the project).

Auto-classify to Eng Excellence by default:
- Incident response / production fixes (e.g. "HTTP 504 alerts resolved", "XxxException investigation")
- Capacity planning / failure analysis (e.g. "throughput spike analysis")
- Routing / escalation work
- Ticket processing
- Minor BAU support items (ad-hoc help, validation logic MRs)
- Standalone documentation NOT tied to a current feature delivery (e.g. user guidance, FAQ updates)
- Hiring / interviews

Keep under the project (NOT Eng Excellence):
- Issue fix that materially advances a Key Feature of an in-progress project
- Documentation co-shipped with a feature (RFC complete, design doc for a milestone)

After mapping, **show the BAU candidate list** and ask:

```
Proposed Eng Excellence items (press enter to accept all, or list IDs to reassign):
  [1] HTTP 504 alerts on long-running Task endpoint resolved (Armel)
  [2] Reduce log volume -18% for user-service (Armel)
  [3] Async HTTP callback guidance doc (Armel)
  [4] Capacity planning: 31 May schedule spike analysis (Armel)
  [5] xxx template followup (Willy)
  [6] domain multi-index help (Willy)
  [7] template validation logic MR (Willy)
  [8] 1 candidate interview (Danny)

Reassign? [enter / 3,4 → project-x / ...]
```

User can press enter to validate all, or specify items to reassign.

### 1.5 Show mapping table and confirm

Present a table per product:

```
=== PRODUCT A ===
Project (display name)              | Tasks
------------------------------------|-----------------------------------
Product A - Migration               | 5 tasks (Harry, Karine, Willy)
Reload from Archive.                | 3 tasks (Harry, Willy)
XXX Pilot                           | 2 tasks (Mary)
Cluster Migration                   | 1 task (Karine)
[Eng Excellence]                    | 4 tasks (BAU, support, hiring)

=== PRODUCT B ===
...

Confirm mappings? [y / edit]
```

**Wait for confirmation before proceeding.**

---

## Step 2 — Data Collection (Target Dates & Highlights)

**Goal:** For each mapped project, ensure we have (a) a current target date and
(b) a draft list of highlights / lowlights to mention.

### 2.1 Target dates

For each project in the mapping:

- Read its portal.md entry. If `Target:` is **missing or empty**, ask:

  ```
  No target date set for project: <Display Name> (project-x)
  When is the next milestone? (e.g. "Mid June", "Q3", "End of Q2")
  ```

- Once provided, **update portal.md** by editing the entry to include
  `— Target: <date>` (append after Alias if not present).

### 2.2 Highlights candidate generation

For each project mentioned this week:

1. Read the project page (e.g. `wiki/projects/product-a/.../project-x.md`).
2. Find the `## Key Features` checklist. Each `- [ ]` line is a tracked feature.
3. From this week's tasks, identify which align with a Key Feature.
4. If a project does not have a `## Key Features` section, **ask the user**:

   ```
   project-x has no `## Key Features` section.
   What features should I track for it? (bulleted list, I'll add it to the project page)
   ```

   Once provided, edit the project page to add the section.

### 2.2.1 Highlight admission criteria (Pattern: stakeholder filter)

An item qualifies as a **Highlight / Lowlight** only if it has:

- **End-user impact** (a customer, domain team, or partner team is materially affected — new capability, behavior change, outage, regression), OR
- **Significant release** (production cutover, GA milestone, major migration completed, RFC ratified, deprecation closed)

Items that DO NOT qualify as highlights stay in their project's Key Projects section OR Eng Excellence:

- Internal efficiency wins (internal latency improvements, log volume reductions, code refactors)
- Single-component fixes that don't change product behavior
- Tooling / dev-platform improvements without user-facing change
- Documentation produced

When in doubt: keep it OUT of highlights. Highlights aim for **2–4 items maximum** across both products.

### 2.3 Draft Highlights / Lowlights

Produce a draft of **2–4 highlights/lowlights maximum**, combining both products.

```
Draft Highlights / Lowlights:
- :tada: Domain fully adopted to new service on prod
- :tada: Product feature migrated successfully from legacy service for XX teams
- :bomb: Heavy query by domain team triggered circuit breaker (recovered)

Confirm or edit? [y / edit]
```

**Wait for confirmation before proceeding.**

---

## Step 3 — Feature Completion Tracking

**Goal:** Roll forward each project's `## Key Features` checklist based on this
week's deliveries, and decide which projects (if any) are now Complete.

**Skip projects with zero activity this week** — do not surface them in the diff.

### 3.0 Key Features state model (3 states)

The schema supports three states for each `## Key Features` line:

| Visual                                    | Meaning                                       |
| ----------------------------------------- | --------------------------------------------- |
| `- [ ] Feature text`                      | Not started / planned                         |
| `- [ ] Feature text [:work_in_progress:]` | Active this week, NOT yet done                |
| `- [x] Feature text`                      | **Accomplished and no further action needed** |

**Critical rule:** `- [x]` is only used when the feature is **fully accomplished with no follow-up required**. It is NOT used for intermediate progress, micro-updates, partial deliveries, or "good progress this week."

For ongoing or partially-delivered features, leave `- [ ]` and append ` [:work_in_progress:]`. If the feature spans many or complex actions, **break it into subtasks** rather than over-ticking:

```
- [ ] Domain team migration (Identity management) [:work_in_progress:]
    - [x] Sample pipeline set up (staging)
    - [x] Onboarding kickoff with Identity team
    - [ ] Staging pipeline operationalised
    - [ ] Production cutover
```

### 3.1 Build the project-page diff

For each project that had activity this week, classify each existing Key Feature and each new task:

1. **Existing `- [ ]` features** — does this week's activity:
   - Fully accomplish it (no follow-up)? → propose **tick to `[x]`**
   - Make active progress without finishing? → propose **add `[:work_in_progress:]` marker**
   - Touch nothing? → no change
2. **Existing `- [ ] ... [:work_in_progress:]` features** — does this week's activity:
   - Fully accomplish it? → propose **tick to `[x]` and remove `[:work_in_progress:]`**
   - Continue progress? → no change
3. **New tasks that don't map to a Key Feature** — does the work represent:
   - An ongoing stream / multi-week initiative? → propose **add as a new `- [ ]` (or `- [ ] [:work_in_progress:]`) feature**
   - Complex enough that one feature is too coarse? → propose **add as feature with subtasks**
   - Tactical / one-off? → no change (handled in weekly file only)

### 3.2 Show the diff preview and confirm all at once (Pattern: batched approval)

Show ALL proposed project-page changes in a single diff preview, then ask once:

```
=== Proposed project-page changes ===

project-xx:
  ~ [ ] Task A
  → [ ] Task B [:work_in_progress:]
      + subtasks:
        - [x] Task C (staging)
        - [x] Task D
        - [ ] Task E
        - [ ] Task F

=== Projects marked Complete? ===
(none this week)

Apply all changes? [enter / per-item edit / skip]
```

User can press enter to accept everything, request edits, or skip individual items.

### 3.3 Project completion check

After applying ticks, if **ALL** Key Features for a project are `[x]` (no `[:work_in_progress:]` markers, no subtasks open):

```
Project: <Display Name> — all tracked features are accomplished.
  a) Mark project as Complete (status → Complete, add :checked: in reports)
  b) Add new features (provide list)
```

- If (a): update project page YAML/status to "Complete" and add `:checked:` after
  the project name in the wiki file (Step 4). This `:checked:` marker carries
  through to the consolidated report in Phase 2.
- If (b): append new `- [ ]` features and keep project status In Progress.

---

## Step 4 — Write Wiki Weekly Reports

**Goal:** Write the two per-product wiki files. These are the handoff artifacts
consumed by `weekly-2-consolidate`.

### 4.1 File naming

- `wiki/projects/_weekly_/<date>-product-a.md`
- `wiki/projects/_weekly_/<date>-product-b.md`

### 4.2 Wiki file format (per product)

```markdown
---
Category: weekly
Tags:
  - weekly-update
  - <year>-q<1-4>
  - "#project/active/<product>"
Product:
  - "[[<product>]]"
Collaborators:
  - "[[<Contributor1>]]"
  - "[[<Contributor2>]]"
Description: Weekly digest of <date> for <Product> team covering key updates, project progress, and support work.
Created: <date>
Last Updated: <date>
---

**Tech Platform - <Product>** Week of <date>

## Highlights / Lowlights

- <Highlight or lowlight 1>
- <Highlight or lowlight 2>

## Key Projects

- :large_green_circle: [[project-x|Display Name]] :checked:
    - [:done:] <Completed task>
    - [:work_in_progress:] <In-progress task>
    - [:todo_new:] <Planned task>

- :large_green_circle: [[project-y|Display Name]]
    - [:done:] <Completed task>

## Eng Excellence

- :large_yellow_circle: Support / BAU load — <X>%
    - <Support item 1>
    - <Support item 2>
- :large_yellow_circle: Hiring
    - [:done:] <N> candidate interview(s)

## Related

- [[<date>-<product>|Previous week: <product> <prev-date>]]
```

**Conventions:**

- Use `[[project-x|Display Name]]` link format with the alias from portal.md as the display label.
- Project health: `:large_green_circle:` (on track), `:large_yellow_circle:`
  (some blockers), `:red_circle:` (blocked).
- Task status: `[:done:]`, `[:work_in_progress:]`, `[:todo_new:]`, `[:blocked:]`.
- If project is marked Complete in Step 3, append ` :checked:` after the
  `[[project-x|Display Name]]` link.
- Quarter tag: `<year>-q<1-4>` based on the date.

### 4.3 (Optional) Source page

If the previous workflow tracked per-contributor source pages, also write
`wiki/sources/weekly-<product>-<date>.md` with the per-contributor breakdown.
This is OPTIONAL — skip unless explicitly requested or if the previous week had one.

### 4.4 Previous-week Related link

Calculate the previous week's date. If `<prev-date>-<product>.md` exists,
add a `## Related` link to it. If not, omit the section.

---

## Post-Phase Bookkeeping

After Steps 1–4 are complete and confirmed:

### Update portal

In `wiki/portal.md` under the `## Sources` section, add:

```markdown
- [[weekly-product-a-<date>|Weekly: Product A <date>]] — A team weekly (<short summary>)
- [[weekly-product-b-<date>|Weekly: Product B <date>]] — B team weekly (<short summary>)
```

### Update log

Append to `wiki/log.md`:

```markdown
## [<date>] ingest | Weekly Product A + Product B <date> (aggregate)

Aggregated weekly updates for Product A and Product B teams into per-product wiki pages.

**Contributors:** Product A <N1> · Product B <N2>
**Created:** <date>-product-a.md, <date>-product-b.md
**Projects updated:** <list>
**Features ticked / projects completed:** <summary>
```

### Report to user & handoff

```
Phase 1 (aggregate) complete. Created:
- wiki/projects/_weekly_/<date>-product-a.md
- wiki/projects/_weekly_/<date>-product-b.md

Project pages updated:
- <project-x>: <N> features ticked
- <project-y>: marked Complete

Portal updated: target dates for <list>

Next: run /weekly-2-consolidate <date> to produce the Slack-ready final report.
```

---

## Conventions Summary

- **Strict project grouping:** only projects from `wiki/portal.md`. Child > parent
  when match is specific.
- **Emoji normalization:** Slack image URLs → text emoji in all wiki outputs.
- **Wiki link in wiki files:** `[[project-x|Display Name]]`.
- **Target dates** live in portal.md; ask before assuming.
- **Key Features 3-state model:**
  - `- [ ]` — not started / planned
  - `- [ ] ... [:work_in_progress:]` — active this week, NOT yet done
  - `- [x]` — fully accomplished, no follow-up required (NEVER for intermediate progress)
  - Use subtasks when work is complex or multi-phase.
- **Eng Excellence default:** Operational, incident, capacity, hiring, routing, and ticket work goes to Eng Excellence — UNLESS it materially advances a Key Feature of an in-progress project.
- **Highlight admission:** `## Highlights / Lowlights` is reserved for items with end-user impact OR significant releases. Internal efficiency wins stay in project sections or Eng Excellence.
- **Quarter tag:** `<year>-q<1-4>` based on date.
- **Previous week link** in `## Related` if available.
- **`:checked:`** indicator after a project name when the project is marked Complete
  — carries through to the consolidated report in Phase 2.

## Edge Cases

- **Multiple team files:** A `<date> Team <product>.md` file = a single
  contributor named "Team".
- **Missing Eng Excellence:** Omit the section for that contributor.
- **No highlights provided:** Promote the top `[:done:]` item.
- **BAU range (e.g. "10-15%"):** keep the range in the wiki file.
