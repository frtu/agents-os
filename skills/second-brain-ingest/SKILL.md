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

## Before Processing: Read Categorization Rules

**IMPORTANT**: Before categorizing any content, read the categorization guide:

- `docs/wiki-architecture.md` — category articulation, decision flowcharts, examples, and ambiguous case resolution

This guide explains:
- How categories relate to each other (Concepts → Product → People → Resources → Projects)
- Decision flowchart for choosing the right category
- Concrete examples and edge cases
- Ambiguous case resolution (e.g., persona vs member, feature vs process vs artifact)

Use this as your primary reference for categorization decisions.

## Process Each Source

For each source file, follow this workflow:

### 1. Read the source completely

Read the entire file. If the file contains image references, note them — read the images separately if they contain important information.

### 2. Present brief summary and gather context (for single clipping documents)

**For single web clipping files from `raw/clippings/`:**

Before writing anything, present:
- **Brief summary** (2-3 sentences) of what the document covers
- **Relevance check**: Ask if this is relevant to the vault's topic/domain
- **Enrichment opportunity**: Ask if any additional tags, categories, or context should be added

Example prompt:
> "I read [filename]. Brief summary: [2-3 sentence summary].
>
> Is this relevant to [vault domain]? Should I add any specific tags or context to enrich this document before processing?"

Wait for user response before proceeding.

**For other source types** (docs, notes, or multiple files):
Share the 3-5 most important takeaways from the source. Ask the user if they want to emphasize any particular aspects or skip any topics. Wait for confirmation before proceeding.

### 3. Create source summary page

Create a new file in `wiki/sources/` named after the source (slugified). Include:

### 4. Extract and categorize content

**CRITICAL**: Use the decision flowchart in `docs/wiki-architecture.md` to determine the correct category for each piece of content. The flowchart asks:

1. Is it theoretical/reusable domain knowledge? → `concepts/`
2. Is it a definition of what we want to do? → `product/`
3. Is it related to who does it or how to do it? → `people/`
4. Is it something produced or used? → `resources/`
5. Is it concrete time-bounded work? → `projects/`

Analyze the source and categorize content into the appropriate wiki subdirectories:

**Conceptual content** → `wiki/concepts/`
- `wiki/concepts/patterns/` — development patterns and principles (e.g., idempotency, reliability, feedback-loops)
- `wiki/concepts/technologies/` — reusable frameworks and methodologies (e.g., Kafka, OKR, career-ladder, agile)

**Product content** → `wiki/product/`
- `wiki/product/entities/` — business objects and models (e.g., accounts, users, property, lease)
- `wiki/product/features/` — functional capabilities (e.g., account-management, hiring, performance-review)
- `wiki/product/persona/` — role categories and user types (e.g., ops-team, engineering-manager, student-renter)
  - **IMPORTANT**: Personas are role categories, NOT individuals. Named people go in `people/members/`

**People content** → `wiki/people/` — **For career ladder, competency, and process sources, prefer using `/people-ingest` skill which has specialized formats and cross-linking.**
- `wiki/people/processes/` — workflows to achieve outcomes (e.g., software-engineering, hiring-process, property-acquisition)
- `wiki/people/steps/` — granular actions within processes (e.g., development, interviewing, property-viewing)
- `wiki/people/competencies/` — hard or soft skills (e.g., system-design, leadership, negotiation). Includes category pages and individual skill pages with depth progression tables.
- `wiki/people/roles/` — career ladder roles with levels and tracks. Use naming pattern `role-<track>-<level>.md` (e.g., `role-ic-3.md` for IC track 3, `role-mgmt-2.md` for management track 2). See `people-ingest` skill for role page format.
- `wiki/people/members/` — named individuals (e.g., fred, alice-engineering-manager, lawyer-dupont)
  - **IMPORTANT**: Members are specific people, NOT role categories. Role categories go in `product/persona/`

**Resource content** → `wiki/resources/`
- `wiki/resources/artifacts/` — outputs and deliverables (e.g., source-code, performance-review-document, financing-plan, deployment-pipeline)
- `wiki/resources/components/` — internal systems we build (e.g., performance-review-system, yield-calculator). **See Component Page Structure in `second-brain` skills `references/wiki-schema.md`.**
- `wiki/resources/dependencies/` — external systems we depend on (e.g., hr-system, bank, notary)
- `wiki/resources/tools/` — ready-to-use applications (e.g., JIRA, Lattice, SeLoger)

**Project content** → `wiki/projects/`
- `wiki/projects/{initiative-name}/` — transversal initiatives (e.g., kafka-migration, tax-optimization)
- `wiki/projects/{product-name}/` — product grouping (e.g., account-management)
- `wiki/projects/{product-name}/{project-name}/` — specific projects (e.g., account-management/new-customer-onboarding, le-mans/10-rue-nationale)

**Synthesis content** → `wiki/synthesis/`
- Cross-cutting analyses and comparisons (e.g., technology comparisons, ADRs, benchmarks)

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

## Categorization Best Practices

**ALWAYS consult `docs/wiki-architecture.md` when uncertain about categorization**. Common pitfalls:

### Persona vs Member
- **Persona** (in `product/persona/`): Role category (e.g., engineering-manager, student, beginner-investor)
- **Member** (in `people/members/`): Named individual (e.g., fred, alice-engineering-manager, lawyer-dupont)

### Entity vs Persona
- **Entity** (in `product/entities/`): Business object manipulated by features (e.g., lease, property, tenant)
- **Persona** (in `product/persona/`): User type with specific needs (e.g., student, domain-developer)
- Example: `renter` is an entity (contractual party), `renter-student` is a persona (student renter profile)

### Feature vs Process vs Artifact
- **Feature** (in `product/features/`): Capability offered (e.g., performance-review, yield-calculation)
- **Process** (in `people/processes/`): Workflow to achieve outcome (e.g., performance-review-cycle, property-acquisition)
- **Artifact** (in `resources/artifacts/`): Output produced (e.g., performance-review-document, financing-plan)

### Technology vs Dependency vs Tool
- **Technology** (in `concepts/technologies/`): Abstract capability (e.g., kafka, land-registry)
- **Dependency** (in `resources/dependencies/`): Concrete system we depend on (e.g., kafka-cluster, hr-system, bank)
- **Tool** (in `resources/tools/`): Usable interface (e.g., kafka-cli, workday, seloger)

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
