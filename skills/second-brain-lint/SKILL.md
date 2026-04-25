---
name: second-brain-lint
description: >
  Health-check the wiki for contradictions, orphan pages, stale claims,
  and missing cross-references. Use when the user says "audit",
  "health check", "lint", "find problems", or wants to improve wiki quality.
allowed-tools: Bash Read Write Edit Glob Grep
---

# Second Brain — Lint

Health-check the wiki and report issues with actionable fixes.

**Read the canonical wiki rules first:**
- `docs/wiki-schema.md` — directory structure, page naming, wikilink conventions
- `people-ingest` skill's `references/people-schema.md` — people page formats (roles, competencies, steps)

Use these as the source of truth for all validation rules.

## Audit Steps

Run all checks below, then present a consolidated report.

### 1. Broken wikilinks

Scan all wiki pages for `[[wikilink]]` references. For each link, verify the target page exists. Report any broken links.

```bash
# Find all wikilinks across wiki pages
grep -roh '\[\[[^]]*\]\]' wiki/ | sort -u
```

Cross-reference against actual files in `wiki/`.

### 2. Orphan pages

Find pages with no inbound links — no other page references them via `[[wikilink]]`.

For each `.md` file in all wiki subdirectories (check `docs/wiki-schema.md` for complete list):
- Extract the page name (filename without extension)
- Search all other wiki pages for wikilinks matching that page
- If no other page links to it, it's an orphan

### 3. Contradictions

Read pages that share topics and look for conflicting claims. Flag when:
- Two pages make opposing claims about the same topic
- Dates, figures, or factual claims differ between pages
- Information from different sources conflicts

### 4. Stale claims

Cross-reference source dates with wiki content. Flag when:
- A page cites only old sources and newer sources exist on the same topic
- Page information hasn't been updated despite newer sources mentioning that topic

### 5. Missing pages

Scan for `[[wikilinks]]` that point to pages that don't exist yet. These are topics the wiki mentions but hasn't given their own page.

Check wikilink format matches convention in `docs/wiki-schema.md`:
- **Single word**: `[[Word]]`
- **Multiple words**: `[[file-link|Display Text]]`
- **Inside tables** (THIS IS IMPORTANT): escape the `|` in wikilinks with `\|` to avoid collision with table column separators — e.g., `[[domain-developer\|Domain Developer]]`

Assess whether missing pages warrant creation.

### 6. Missing cross-references

Find pages that discuss the same topics but don't link to each other. Look for:
- Product pages that mention concepts or resources without linking them
- Concept pages that mention tools or technologies without linking them
- Pages that cover the same topic but don't reference each other

### 7. Index consistency

Verify `wiki/portal.md` is complete and accurate per `docs/wiki-schema.md`:

- Every page in wiki subdirectories has an index entry (check wiki-schema.md for complete category list)
- No index entries point to deleted pages
- Entries are under the correct category header (see Index Format in wiki-schema.md)

### 8. Category placement

Verify pages are in the correct subdirectory based on their content type per `docs/wiki-schema.md`.

Read the Wiki subdirectories section in wiki-schema.md for the complete category mapping (Product, People, Concepts, Resources, Projects).

Special naming patterns to check:
- Steps: `step-{name}.md` (defined in people-schema.md)
- Roles: `role-<track>-<level>.md` (e.g., `role-ic-3.md`, `role-mgmt-2.md`)

Flag any pages that appear to be miscategorized.

### 9. People-specific validation

For `wiki/people/` content, verify structure matches `people-ingest` skill's `references/people-schema.md`.

Read people-schema.md for complete validation rules for:
- **Role pages** — Level Differentiation, competency tables, skill links with section anchors
- **Competency/Skill pages** — IC/M-Track depth progression tables, role references, SDLC Application
- **Step pages** — parent process links, skill references
- **Cross-linking** — roles ↔ skills ↔ steps bidirectional references


### 10. Data gaps

Based on the wiki's current coverage, suggest:
- Topics mentioned frequently but lacking depth
- Questions the wiki can't answer well
- Areas where a web search could fill in missing information

## Report Format

Present findings grouped by severity:

### Errors (must fix)
- Broken wikilinks
- Contradictions between pages
- Index entries pointing to missing pages

### Warnings (should fix)
- Orphan pages with no inbound links
- Stale claims from outdated sources
- Missing pages for frequently referenced topics

### Info (nice to fix)
- Potential cross-references to add
- Data gaps that could be filled
- Index entries that could be more descriptive

For each finding, include:
- **What:** description of the issue
- **Where:** the specific file(s) and line(s)
- **Fix:** what to do about it

## After the Report

Ask the user:
> "Found N errors, N warnings, and N info items. Want me to fix any of these?"

If the user agrees, fix issues and report what changed.

## Log the lint pass

Append to `wiki/log.md`:

    ## [YYYY-MM-DD] lint | Health check
    Found N errors, N warnings, N info items. Fixed: [list of fixes applied].

## When to Lint

- **After every 10 ingests** — catches cross-reference gaps while they're fresh
- **Monthly at minimum** — catches stale claims and orphan pages over time
- **Before major queries** — ensures the wiki is healthy before you rely on it for analysis

## Related Skills

- `/second-brain-ingest` — process new sources into wiki pages
- `/people-ingest` — process people-related sources (career ladders, competencies, processes)
- `/second-brain-query` — ask questions against the wiki
