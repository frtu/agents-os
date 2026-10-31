---
name: second-brain-reorg
description: >
  Reorganize, refactor or restructure a second-brain wiki: split a folder node
  into theme areas (pillars) derived from the vault's purpose, impose a
  user-defined taxonomy, or carve a cross-cutting theme into its own dedicated
  domain across parents. Use when the user says "reorganize this folder into
  areas", "group these by theme/pillar", "organise folder X based on the vault
  purpose", "refactor this folder", "split into categories", "introduce new
  taxonomy", "create a new area", "add a capability domain", "group the X
  concepts into their own folder", or names a wiki node (e.g. `product`,
  `concepts`, `resources/artifacts`) to restructure. Differs from
  /second-brain-ingest (files new pages, doesn't restructure) and
  /second-brain-lint (health-checks content, doesn't move files).
allowed-tools: Bash Read Write Edit Glob Grep Agent AskUserQuestion
---

# Second Brain — Reorg

Reorganize the second brain's structure. Three modes, selected by what the user brings to the table:

| Mode | Situation | Who proposes the structure |
|------|-----------|---------------------------|
| **A — Theme areas** | A flat folder grew organically and needs meaningful grouping (e.g. `resources/artifacts/` → hiring / career / project / governance) | The model, from folder content + the vault's purpose; user confirms |
| **B — User taxonomy** | The user already knows the categories to impose | The user; the skill classifies files and executes |
| **C — Carve an area** | One cross-cutting theme deserves its own dedicated space across parents (e.g. a new product domain + a `concepts/patterns/{area}/` subfolder) | The model scopes the area; user confirms |

All modes share one execution core: **propose → confirm → `git mv` (never rewrite bodies) → routing README → portal/log → stage**.

## Why moves are safe

Obsidian resolves `[[wikilinks]]` by **filename**, not path. Moving a page into a subfolder does **not** break inbound links, as long as filenames stay unique across the vault. So this skill only *moves* files — it never rewrites their bodies (frontmatter/metadata headers are the one exception, see Step 2c). Always move with `git mv` so history is preserved and the change reads as a rename.

## Workflow

### Step 0: Resolve the scope

1. **User proposed a scope (categories or an area)?** Use it — **Mode B** if they named a set of categories for a folder, **Mode C** if they named a single theme to carve out. Keep their names verbatim and skip to Step 1's fan-out.
2. **User named a folder node?** Use it — **Mode A**.
3. **Otherwise ask which node of the wiki folder tree to reorganize.** Offer the core folders plus free text:
   - `wiki/product/` · `wiki/people/` · `wiki/concepts/` · `wiki/resources/` (or a subfolder like `resources/artifacts`) · `wiki/projects/` · `wiki/synthesis/`
4. **Vault purpose (target system).** Read the vault's `README.md` or `AGENTS.md` — the top section (often quoted) names the purpose. Write it back in one sentence. The proposed areas MUST map to this purpose, not to generic taxonomy.
   - Example: `management` → "shape the team so they succeed" → pillars are SDLC · Hiring · Coaching · Performance · Advocacy.
5. **Inventory the folder.** List every file and note any existing README:

```bash
find wiki/{target-folder} -type f | sort
```

If the folder is already deeply nested or has < 6 loose files, tell the user grouping may not be worth it and confirm they still want to proceed.

### Step 1: Read foundations, then fan out sub-agents

**Main agent reads:**

- Vault `README.md` or `AGENTS.md` — the purpose (Modes A and C)
- `docs/wiki-schema.md` — **when it exists**, the folder/naming rules a proposal must respect
- `wiki/{folder}/README.md` — an existing routing table gets **enriched**, not replaced
- `wiki/portal.md` — the folder's current index section
- Mode C only: `wiki/product/README.md` (how domains are registered) and one existing domain README (the exact shape to mirror)

**Fan out read-only sub-agents to analyze the content in parallel — especially when proposing structures.** The main agent stays the sole writer and sole decision-maker; sub-agents only read and report.

- Split the file list into batches (roughly 5–8 files per agent, or one agent per obvious candidate cluster).
- Launch the batches **in parallel** — one `general-purpose` (or `Explore`) Agent per batch in a single message.
- Brief each agent with: the **vault purpose** (Step 0), its file list, and this extraction goal:

> "For each file, read the frontmatter and first section. Report, per file: (1) a one-line summary, (2) which pillar of the vault purpose it serves, (3) 2–4 candidate theme tags. Keep the whole report under ~600 words. Do not write or move anything."

**Then synthesize the proposal (main agent):**

- **Mode A** — cluster into the **fewest coherent areas** that each map to a pillar of the vault purpose. Prefer **4–6 areas**; fold singletons into the nearest pillar unless genuinely sui generis. Every file lands in exactly one area (mutually exclusive, collectively exhaustive).
- **Mode B** — take the user's categories; if they want inspiration, offer patterns by folder type:
  - `product/`: by audience (end-user, developer, admin), by lifecycle, by domain
  - `people/`: by role type (IC, management), by seniority, by function
  - `concepts/`: by abstraction level, by domain, by maturity
  - `resources/`: by ownership, by lifecycle, by technology
- **Mode C** — establish the **area slug** (kebab-case) + Title Case name, a MECE scope, its relationship to adjacent domains, and **what does NOT belong** (with the correct alternative folder for each exclusion). Find scattered pages on the theme and confirm topical fit:
  ```bash
  qmd search "{area terms}" --path wiki/concepts/ --path wiki/resources/
  ```
  Regroup only where a **named subfolder is an established convention** for that parent (e.g. `concepts/patterns/` already contains theme subfolders).

Present the proposal as a grouping table and confirm with **AskUserQuestion** (let the user rename/merge/split):

| Area (folder) | Pillar | Description (for README) | Files |
|---------------|--------|--------------------------|-------|
| `hiring/` | Hiring | Interview rubrics, evaluation frameworks, feedback templates | 7 |
| ... | ... | ... | ... |

No file is moved before the user confirms. Honor merges/renames they request. For ambiguous classifications, present a confidence table and ask.

### Step 2: Execute the reorganization

**2a. Create folders and move files with `git mv`** (batch per area):

```bash
cd wiki/{target-folder}
mkdir -p {area1} {area2} {area3} ...
git mv file-a.md file-b.md {area1}/
git mv file-c.md {area2}/
...
```

Verify nothing was left behind or duplicated:

```bash
find . -type f | sort
```

**Mode C additionally** — scaffold the product capability domain, seeding empty subfolders with `.gitkeep`:

```bash
cd wiki/product
mkdir -p {area}/entities {area}/features {area}/persona
touch {area}/{entities,features,persona}/.gitkeep
```

Write `wiki/product/{area}/README.md` mirroring an existing domain README, with sections: **Scope** (inclusion criteria), **Structure** (persona/entities/features and their roles), **Articulation** (how personas use features, features consume entities, features are implemented by components, patterns guide implementation), **Relationship to the adjacent domain**, and **What Does NOT Belong Here** (exclusion → correct folder). Register the domain in the **Domains** list of `wiki/product/README.md`, matching the existing entries' format.

**2b. Write or enrich the routing README.** Check for existing schema first:

- `wiki/{folder}/README.md` already carries a routing table → **enrich it**: add or adjust rows for the new areas, keep the existing language.
- No routing README, but `docs/wiki-schema.md` documents this folder → update the schema doc **and** add the README table (both stay consistent).
- Neither exists → **create** `wiki/{folder}/README.md` with the routing table:

```markdown
{One-paragraph description of what this folder holds.}

## Theme folders

Organized by the pillar each {item} serves. **When ingesting a new {item}, place it in the matching folder below.** If none fits, propose a new theme folder rather than dropping it at the root.

| Folder | Pillar | Holds | Examples |
|--------|--------|-------|----------|
| `{area1}/` | {pillar} | {what belongs} | `{example-slug}`, ... |

## What counts as a {item}
{Optional: the inclusion test / custom-vs-standard rule for this folder.}
```

The **"When ingesting … place it in the matching folder"** line is load-bearing — `second-brain-ingest` reads this table to route new pages (see its Step 5). Keep the table's language actionable.

**2c. Metadata headers only.** Page bodies are untouched. Frontmatter/metadata headers (`Category:`, `Tags:`, …) **may** be updated so they reflect the new taxonomy — this is the only permitted in-file change. Run the same rule for pages moved in Mode C.

### Step 3: Update indexes and schema

- **`wiki/portal.md`.** Split the folder's flat index section into themed sub-headings mirroring the new areas (use `####` sub-headings under the existing `###` section). While here, **drop any broken index links** to pages that no longer exist — verify with:
  ```bash
  for l in $(...slugs...); do find wiki -name "$l.md" | grep -q . || echo "BROKEN: $l"; done
  ```
- **`docs/wiki-schema.md` — when the file exists**, extend it: new folder structure under the appropriate section, updated Page Naming examples, updated Index Format if headers changed. If the vault has no schema doc, the folder README is the contract.
- **Path-form links.** Because moves preserve filenames this should be clean, but confirm no page used a full *path* form to a moved file:
  ```bash
  grep -rn "wiki/{target-folder}/[a-z-]*\.md" wiki/ | grep -v "/README"
  ```
  Fix any path-form references to plain `[[slug]]` links.

### Step 4: Log, stage, report

Append a reverse-chronological entry at the top of `wiki/log.md` (after the header):

```markdown
## [YYYY-MM-DD] reorg | {Mode letter: theme-organize {folder} / {folder} restructure / create area {area}}

{One paragraph: what was reorganized, into what, and why it maps to the vault purpose.}
File moves only (via `git mv`) — no body rewrites; frontmatter updated where noted; `[[wikilinks]]` resolve by filename so all cross-links stayed intact.

**Areas created ({M}):**
- `{area1}/` ({count}) — {what}

**Pages Updated:**
- `wiki/{folder}/README.md` — {created|enriched} theme-routing table for future ingests
- [[portal]] — {folder} section split into themed sub-headings{; removed broken link X}
- `docs/wiki-schema.md` — {summary of the extension}
```

Stage all changes via `/change-management-1-stage` (which chains into `/change-management-9-log`; do not commit unless asked):

```
/change-management-1-stage
  trigger: {user's original instruction}
  operation: reorg
  subject: {folder | area}
  input_files: (none — folder reorganization)
  created_files: {area folders + README.md, Mode C: domain scaffold}
  updated_files: {folder}/README.md, portal.md, log.md{, docs/wiki-schema.md}
```

Report results:

- ASCII tree of the new structure
- File count per area
- Any broken links removed, any path-form links fixed, any frontmatter updated
- Reminder: `second-brain-ingest` will now route new pages into these areas via the README

## Validation Checklist

- [ ] Scope resolved: user proposal honored verbatim, or model proposal derived from vault purpose + content
- [ ] Every file lands in exactly one area (mutually exclusive, collectively exhaustive)
- [ ] All moves via `git mv` — history preserved; bodies unchanged; only frontmatter touched
- [ ] Mode C: `product/{area}/` has `persona/`, `entities/`, `features/` (`.gitkeep` when empty); domain README has Scope, Structure, Articulation, What Does NOT Belong Here; registered in `product/README.md`; subfolder grouping follows an existing convention for that parent
- [ ] Routing README created or enriched; existing tables enriched, never replaced
- [ ] `portal.md` updated with themed sub-headings; broken links dropped
- [ ] `docs/wiki-schema.md` extended when it exists
- [ ] No path-form links to moved files remain
- [ ] `log.md` appended; changes staged via `/change-management-1-stage`

## Conventions

- **Propose, then confirm.** Never move files before the user confirms area names + membership (Step 1). When the user proposes the scope, honor it exactly.
- **Map to the vault purpose, not generic taxonomy.** Areas are the vault's pillars, derived from `CLAUDE.md` — unless the user imposed their own taxonomy.
- **Move, never rewrite.** `git mv` only. Bodies untouched; frontmatter/metadata headers may be updated to the new taxonomy.
- **Fewest coherent areas.** Prefer 4–6; fold singletons into the nearest pillar unless genuinely distinct.
- **Leave a routing README.** The README's routing table is the contract `second-brain-ingest` uses to file future pages. Enrich an existing one; don't replace it.
- **Fan out for analysis.** Sub-agents read in parallel; the main agent synthesizes, decides and writes.

## Related Skills

- `/second-brain-ingest` — files new pages using the folder README routing table; populates a Mode C area from raw sources
- `/second-brain-lint` — health-check the wiki after a large reorg
- `/research-deep` — after a Mode C carve-out, research and write the missing entity/feature/persona pages
- `/change-management-1-stage` — stage the reorganization (chains into `-9-log`)
