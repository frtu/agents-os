---
name: second-brain-ingest
description: >
  Process raw source documents into wiki pages. Use when the user adds
  files to raw/ and wants them ingested, says "process this source",
  "ingest this article", "I added something to raw/", or wants to
  incorporate new material into their knowledge base.
allowed-tools: Bash Read Write Edit Glob Grep
---

# Second Brain — Ingest

Process raw source documents into structured, interlinked wiki pages.

## Identify Sources to Process

Determine which files need ingestion:

1. If the user specifies a file or files, use those
2. If the user says "process new sources" or similar, detect unprocessed files:
   - List all files in `raw/` (excluding `raw/assets/`)
   - Read `wiki/log.md` and extract all previously ingested source filenames from `ingest` entries
   - Any file in `raw/` not listed in the log is unprocessed
3. If no unprocessed files are found, tell the user

## Process Each Source

For each source file, follow this workflow:

### 1. Read the source completely

Read the entire file. If the file contains image references, note them — read the images separately if they contain important information.

### 2. Discuss key takeaways with the user

Before writing anything, share the 3-5 most important takeaways from the source. Ask the user if they want to emphasize any particular aspects or skip any topics. Wait for confirmation before proceeding.

### 3. Create source summary page

Create a new file in `wiki/sources/` named after the source (slugified). Include:

### 4. Extract and categorize content

Analyze the source and categorize content into the appropriate wiki subdirectories:

**Product content** → `wiki/product/`
- `wiki/product/persona/` — categories of users (e.g., product-manager, developer)
- `wiki/product/entities/` — product entities, models or logical concepts (e.g., users, accounts)
- `wiki/product/features/` — product-level capabilities or value propositions (e.g., find user by ID)

**People content** → `wiki/people/` — **For career ladder, competency, and process sources, prefer using `/people-ingest` skill which has specialized formats and cross-linking.**
- `wiki/people/processes/` — step of actions to achieve an outcome (e.g., software engineering, regulatory audit)
- `wiki/people/steps/` — a particular step of a process (e.g., development, deployment, release management)
- `wiki/people/competencies/` — hard or soft skills needed (e.g., system design, leadership). Includes category pages and individual skill pages with depth progression tables.
- `wiki/people/roles/` — career ladder roles with levels and tracks. Use naming pattern `role-<track>-<level>.md` (e.g., `role-ic-3.md` for IC track Senior Software Engineer, `role-mgmt-2.md` for management track 2). See `people-ingest` skill for role page format.
- `wiki/people/members/` — individual persons from a squad/team (e.g., fred)

**Conceptual content** → `wiki/concepts/`
- `wiki/concepts/patterns/` — development patterns (e.g., idempotency, dead letter queue, canary deployment)
- `wiki/concepts/technologies/` — reusable technology (e.g., database, Kafka)

**Resource content** → `wiki/resources/`
- `wiki/resources/artifacts/` — things produced by the system (e.g., source code, binary package, pipeline)
- `wiki/resources/components/` — internal system components that deliver user value (e.g., service-a, modelling). **See Component Page Structure in `second-brain` skills `references/wiki-schema.md`.
- `wiki/resources/dependencies/` — dependencies our application depends on (e.g., PVC, Pod, Schema registry)
- `wiki/resources/tools/` — systems human/AI can reuse out of the box (e.g., JIRA, bash commands, Google Docs)

For each page, include YAML frontmatter:

    ---
    Category: [category]
    Tags: [relevant, tags]
    Source links:
    - [original-filename.md]
    Created: YYYY-MM-DD
    Last Updated: YYYY-MM-DD
    ---

    # Page Title

    **Source:** original-filename.md
    **Date ingested:** YYYY-MM-DD
    **Type:** article | paper | transcript | notes | etc.

    ## Summary

    Focused summary based on what the source says about this topic using reference links to other [[topic]] pages.

    ## Related

    - [[related-page|Related Page]] — brief context
    - ...

### 5. Update or create wiki pages

For each topic identified in the source:

**If a wiki page already exists:**
- Read the existing page
- Add new information from this source
- Add the source to the `sources:` frontmatter list
- Update the `updated:` date
- Note any contradictions with existing content, citing both sources

**If no wiki page exists:**
- Create a new page in the most specific appropriate subdirectory
- If no specific subfolder matches, use the parent folder (e.g., `wiki/product/` instead of a subfolder)
- Include YAML frontmatter with tags, sources, created, and updated fields
- Write a focused summary based on what this source says about the topic

### 6. Add wikilinks

Ensure all related pages link to each other using `[[wikilink]]` syntax. Every mention of an entity or concept that has its own page should be linked.

### 7. Update wiki/portal.md

For each new page created, add an entry under the appropriate category header:

    - [[page-name|Page Name]] — one-line summary (under 120 characters)

### 8. Update wiki/log.md

Append:

    ## [YYYY-MM-DD] ingest | Source Title
    Processed [[source-filename.md]]. Created N new pages, updated M existing pages.
    New pages: [[page-1|Page 1]], [[page-2|Page 2]], [[page-3|Page 3]].

### 9. Report results

Tell the user what was done:
- Pages created (with links and their category)
- Pages updated (with what changed)
- Any contradictions found with existing content

## Conventions

- Source summary pages are **factual only**. Save interpretation and synthesis for concept and synthesis pages.
- Wiki pages should be **factual**. Focus on what the source says about the topic.
- A single source typically touches **10-15 wiki pages**. This is normal and expected.
- When new information contradicts existing wiki content, **update the wiki page and note the contradiction** with both sources cited.
- **Prefer updating existing pages** over creating new ones. Only create a new page when the topic is distinct enough to warrant its own page.
- **Always use the most specific subfolder** when creating pages. Fall back to parent folder only when no subfolder matches.
- Use `[[wikilinks]]` for all internal references. Never use raw file paths.
- **Inside tables**, escape `|` in wikilinks: `[[page-name\|Display Text]]` to avoid collision with table column separators.
- **Component pages must follow the Component Page Structure** in `second-brain` skills `references/wiki-schema.md` exactly.

## What's Next

After ingesting sources, the user can:
- **Ask questions** with `/second-brain-query` to explore what was ingested
- **Ingest more sources** — clip another article and run `/second-brain-ingest` again
- **Health-check** with `/second-brain-lint` after every 10 ingests to catch gaps
