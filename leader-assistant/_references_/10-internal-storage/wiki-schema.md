# Wiki Schema

Canonical rules for LLM-maintained knowledge base wikis. This is the single source of truth — agent config templates pull from this document.

## Architecture

Four directories, four roles:

- **raw/** — immutable source documents. The LLM reads from here but NEVER modifies these files.
- **wiki/** — the LLM's workspace. Create, update, and maintain all files here.
- **sessions/** — short-term memory for user/assistant conversation logs. Similar to Claude Code's conversation persistence.
- **output/** — reports, query results, and generated artifacts go here.

### `raw/` directory

Original captured information. The LLM reads from here but **NEVER modifies** these files.

Properties:

- provenance-preserving
- immutable source of truth
- ingestion-triggering
- never treated as synthesized knowledge

#### Raw subdirectories

- `raw/assets/` — images, audio or any resources that doesn't processing but can be used inside Markdown document using syntax `![[resource/path]]`
- `raw/clippings/` — web articles captured with Obsidian Web Clipper or copied manually
- `raw/docs/` — PDFs, papers, received files, reference documents
- `raw/notes/` — handwritten notes, briefs, random ideas
- `raw/transcripts/` — meeting transcripts (Zoom, Teams), voice memo transcripts, interview recordings

### `wiki/` directory

The LLM's workspace. All knowledge processing happens here.

This is the persistent Zettelkasten knowledge layer, organized into six main categories:

- **Concepts** provide reusable patterns and technologies
- **Product** organizes capabilities by type (entities, features, personas)
- **People** define actors, workflows, skills, and actions
- **Resources** track outputs, components, dependencies, and tools
- **Projects** integrate everything into time-bounded work
- **Synthesis** captures cross-cutting analyses

#### Wiki subdirectories

- `wiki/synthesis/` — comparisons, analyses, cross-cutting themes

**Source** — all intermediate capture from raw (mirroring raw/ structure for provenance):
- `wiki/sources/` — one summary page per ingested source, organized by provenance subfolder
  - `wiki/sources/_daily_/` — daily digests produced by dreaming operation
  - `wiki/sources/{provenance}/` — source summaries from `raw/{provenance}/`

**Concepts** — all content related to concepts:
- `wiki/concepts/patterns/` — development patterns (e.g., idempotency, dead letter queue, reliability, canary deployment)
- `wiki/concepts/technologies/` — reusable technology (e.g., MCP, database, Kafka, RAG)

**People** — all content related to team members and their processes. **See `people-ingest` skill's `references/people-schema.md` for detailed people page formats.**
- `wiki/people/processes/` — step of actions to achieve an outcome (e.g., software engineering, regulatory audit)
- `wiki/people/steps/` — a particular step of a process, a particular action to a particular system (e.g., development, deployment)
- `wiki/people/roles/` — career ladder roles with levels and tracks (e.g., role-ic-p3, role-mgmt-m2)
- `wiki/people/competencies/` — hard or soft skills needed to achieve a step of a process (e.g., system design, leadership). Includes category pages and individual skill pages with depth progression tables.
- `wiki/people/members/` — individual persons from a squad/team (e.g., fred)

**Product** — all content related to a product or part of the product this workspace is developing. Anything NOT developed by the team should be stored in `wiki/resources/tools`.

Product capabilities are organized into three flat categories:

- (`wiki/product/`)
  - `wiki/product/persona/` — all user types (e.g., domain-developer, ops-team, platform-sre)
  - `wiki/product/entities/` — all objects and models (e.g., index, query, quota, rate-limit)
  - `wiki/product/features/` — all capabilities (e.g., rate-limiting, universal-search, index-creation)

**Specs** — all content related to product specification:

- `wiki/product/specs/` # Continuously generated specifications
  - 01-product.md       # Core: Product vision
  - 02-domain.md        # Core: Domain model
  - 03-*.md onwards     # MOCs linking to wiki categories

**Resources** — all content related to resources:
- `wiki/resources/artifacts/` — things produced by the system or more physical concepts (e.g., source code, binary package, pipeline)
- `wiki/resources/components/` — internal system components that deliver value to users, including UI components (e.g., service-a, airsearch, observability)
- `wiki/resources/dependencies/` — dependencies our application depends on (e.g., PVC, Pod, Schema registry)
- `wiki/resources/tools/` — runnable systems human/AI can reuse out of the box (e.g., JIRA, bash commands, Google Docs)

**Projects** — all content related to time-bounded development work (initiatives, products, specific projects):
- `wiki/projects/{initiative-name}/` — transversal initiatives (e.g., kafka-migration, sso-enforcement)
- `wiki/projects/{product-name}/` — product or platform (e.g., search-platform)
- `wiki/projects/{product-name}/{project-name}/` — specific project to create or extend product capabilities

Always search the most specific subfolders to write into, or fallback to parent folder when not found.

### Sessions directory

Operational task-specific conversations with human that are captured for short-term continuity.

`sessions/` is **short-term memory** for user/assistant interaction logs and contain:
- Instructions to achieve specific tasks
- Human decisions and judgments (upvotes/downvotes) on knowledge
- Complements and corrections that could improve knowledge maturity

Sessions are **ephemeral operational capture** — not durable knowledge. They feed into the **dreaming** process that extracts valuable insights into daily digests, which then feed into standard ingestion.

Purpose:
- Persist conversation threads across sessions (similar to Claude Code)
- Provide context continuity for the assistant
- Enable conversation search and reference
- Feed valuable exchanges into the ingestion pipeline

Structure:
```text
sessions/
├── 2026-08-12-project-spec.md
├── 2026-08-12-temporal-discussion.md
└── ...
```

Conversations are **not** part of the wiki. They are a separate persistence layer.

**Knowledge promotion follows a two-stage pipeline:**

1. **Dreaming** — daily compaction of sessions into `wiki/sources/_daily_/`
2. **Ingestion** — transfers candidate knowledge from daily digests to wiki categories

This separation keeps sessions operational and ensures only distilled knowledge enters the wiki.

### Special files

- `wiki/portal.md` — master catalog of every wiki page, organized by category. Update on every ingest.
- `wiki/log.md` — append-only chronological record. Never edit existing entries.

## Page Format

Every wiki page MUST include YAML frontmatter:

    ---
    Category: wiki
    Tags: [tag1, tag2]
    Source links:
    - [[source-filename-1.md]]
    - [[source-filename-2.md]]
    Created: YYYY-MM-DD
    Last Updated: YYYY-MM-DD
    ---

Use `[[wikilink]]` syntax for all internal links. When you mention a concept, entity, or source that has its own page, link it.

## Operations

### Dreaming (daily session compaction)

Runs at end of day (or on demand) to compact session conversations into knowledge candidates.

1. Scan all sessions from the current day
2. Extract:
   - **Human decisions**: upvotes, downvotes, corrections, confirmations
   - **Knowledge complements**: new information, refinements, edge cases
   - **Important context**: reasoning behind decisions, constraints discovered
3. Create a daily digest in `wiki/sources/_daily_/YYYY-MM-DD.md`:

```markdown
---
Category: daily-digest
Date: YYYY-MM-DD
Sessions:
- [[session-filename-1]]
- [[session-filename-2]]
Created: YYYY-MM-DD
---

# Daily Digest — YYYY-MM-DD

## Key Decisions
- Decision 1 (from [[session-filename-1]])
- Decision 2 (from [[session-filename-2]])

## Knowledge Candidates

### Candidate 1: [Topic]
**Type**: [correction | complement | new-concept]
**Target**: [[existing-page]] or (new page)
**Content**: [distilled knowledge to transfer]

### Candidate 2: [Topic]
...
```

4. Append to `wiki/log.md`: `## [YYYY-MM-DD] dreaming | Daily digest`

The daily digest serves as **input to standard ingestion**. Session references appear only in the digest — final wiki pages do not reference individual sessions.

### Ingest (processing a new source)

When the user adds a file to raw/ and asks you to process it:

1. Read the source completely
2. Discuss key takeaways with the user
3. Create a source summary page in `wiki/sources/{provenance}/` with: title, source metadata, key claims, and a structured summary
   - If source is from `raw/{provenance}/`, place in `wiki/sources/{provenance}/`
4. Extract and categorize content into the appropriate wiki subdirectories:
   - **Product content**: features, personas, product resources → `wiki/product/`
   - **People content**: processes, steps, competencies, members → `wiki/people/`
   - **Conceptual content**: patterns, technologies → `wiki/concepts/`
   - **Resource content**: artifacts, components, dependencies, tools → `wiki/resources/`
5. For each topic identified:
   - If a wiki page exists: update it with new information from this source
   - If no wiki page exists: create one in the appropriate subdirectory
6. **Knowledge transfer rule**: Final wiki pages (in `concepts/`, `product/`, `people/`, `resources/`) contain standalone knowledge. They reference source summary pages in `wiki/sources/{provenance}/`, but **never reference individual sessions or daily digests directly**. The provenance chain is: `raw/{provenance}/ → sessions/ → wiki/sources/_daily_/ → wiki/sources/{provenance}/{source}.md → wiki/{category}/`
7. Add `[[wikilinks]]` between all related pages
8. Update `wiki/portal.md` with any new pages
9. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | Source Title`

A single source may touch 10-15 wiki pages. That is normal.

### Query (answering questions)

When the user asks a question:

1. Read `wiki/portal.md` to find relevant pages
2. Read the relevant wiki pages
3. Synthesize an answer with `[[wikilink]]` citations to wiki pages
4. If the answer produces a valuable artifact (comparison, analysis, new connection), offer to save it as a new page in `wiki/synthesis/`
5. If you save a new page, update the index and log

### Lint (health check)

When the user asks you to lint or health-check the wiki:

1. Scan for contradictions between pages
2. Find stale claims that newer sources have superseded
3. Identify orphan pages (no inbound links)
4. Find important topics mentioned but lacking their own page
5. Check for missing cross-references
6. Verify pages are in the correct subdirectory based on their content type
7. Suggest data gaps that could be filled with a web search
8. Report findings and offer to fix issues
9. Log the lint pass: `## [YYYY-MM-DD] lint | Summary of findings`

## Index Format

Each entry in `wiki/portal.md` is one line:

    - [[page-name|Page Name]] — one-line summary

Organized under category headers:
- **Product**: Personas, Entities, Features
- **People**: Processes, Steps, Competencies, Roles, Members
- **Concepts**: Patterns, Technologies
- **Resources**: Artifacts, Components, Dependencies, Tools
- **Projects**: Time-bounded initiatives, products, and specific projects
- **Synthesis**: Any report or concept aggregation & summary
- **Sources**: Summary from ingested files

## Log Format

Each entry in `wiki/log.md`:

    ## [YYYY-MM-DD] operation | Title
    Brief description of what was done.

## Page Naming

Filenames use **kebab-case** with `.md` extension. Page titles inside the file use **Title Case**.

Examples:
- Product persona pages: `wiki/product/persona/ops-team.md` → `# Ops Team`
- Product entity pages: `wiki/product/entities/search-template.md` → `# Search Template`
- Product feature pages: `wiki/product/features/universal-search.md` → `# Universal Search`
- Product persona pages: `wiki/product/persona/domain-developer.md` → `# Domain Developer`
- Product entity pages: `wiki/product/entities/index.md` → `# Index`
- Product feature pages: `wiki/product/features/alias-management.md` → `# Alias Management`
- Product persona pages: `wiki/product/persona/infra-t0-team.md` → `# Infra T0 Team`
- Product feature pages: `wiki/product/features/rate-limiting.md` → `# Rate Limiting`
- Process pages: `wiki/people/processes/software-engineering.md` → `# Software Engineering`
- Step pages: `wiki/people/steps/step-{process}-{number}-{name}.md` → `{Process}` should be a one word if no collision (e.g., `sdlc`) `# {Number}. {Step Name}` (e.g., `step-sdlc-1-planning.md` → `# 1. Planning & Initiation`, `step-hire-2-coding.md` → `# 2. Coding Interview`)
- Competency pages: `wiki/people/competencies/system-design.md` → `# System Design`
- Role pages: `wiki/people/roles/role-<track>-<level>.md` → `# <Level> — <Title>` (e.g., `role-ic-p3.md` → `# P3 — Senior Software Engineer`, `role-mgmt-m2.md` → `# M2 — Engineering Manager`)
- Member pages: `wiki/people/members/fred.md` → `# Fred`
- Pattern pages: `wiki/concepts/patterns/idempotency.md` → `# Idempotency`
- Technology pages: `wiki/concepts/technologies/kafka.md` → `# Kafka`
- Artifact pages: `wiki/resources/artifacts/binary-package.md` → `# Binary Package`
- Component pages: `wiki/resources/components/service-a.md` → `# Service A` (see Component Page Structure below)
- Dependency pages: `wiki/resources/dependencies/schema-registry.md` → `# Schema Registry`
- Tool pages: `wiki/resources/tools/jira.md` → `# JIRA`

When creating `[[wikilinks]]`:

- **Single word**: use short form `[[Word]]` — e.g., `[[Kafka]]`, `[[Elasticsearch]]`, `[[JIRA]]`
- **Multiple words**: use long form `[[file-link|Display Text]]` — e.g., `[[create-index|Create Index]]`, `[[30-minute-development-cycle|30-Minute Development Cycle]]`
- **Inside tables** (THIS IS IMPORTANT): escape the `|` in wikilinks with `\|` to avoid collision with table column separators — e.g., `[[domain-developer\|Domain Developer]]`

This keeps single-word links concise while ensuring multi-word links work as file references with human-readable display.

To slugify a title into a filename: lowercase, replace spaces with hyphens, remove special characters, trim to reasonable length.

## Image Handling

Web-clipped articles often include images. Handle them as follows:

1. **Download images locally.** In Obsidian Settings → Files and links, set "Attachment folder path" to `raw/assets/`. Then use "Download attachments for current file" (bind it to a hotkey like Ctrl+Shift+D) after clipping an article.
2. **Reference images from wiki pages** using standard markdown: `![description](../raw/assets/image-name.png)`. Keep the image in `raw/assets/` — never copy images into `wiki/`.
3. **During ingestion**, note any images in the source. If an image contains important information (diagrams, charts, data), describe its contents in the wiki page so the knowledge is captured in text form.

## Lint Frequency

Run a lint pass (`/second-brain-lint`) on this schedule:
- **After every 10 ingests** — catches cross-reference gaps while they're fresh
- **Monthly at minimum** — catches stale claims and orphan pages that accumulate over time
- **Before any major query or synthesis** — ensures the wiki is healthy before you rely on it for analysis

## Tools

You have access to these CLI tools — use them when appropriate:

- **summarize** — summarize links, files, and media. Run `summarize --help` for usage.
- **qmd** — local search engine for markdown files. Run `qmd --help` for usage. Use when the wiki grows beyond what portal.md can efficiently navigate.
- **agent-browser** — browser automation for web research. Use when web_search or web_fetch fail.

## Component Page Structure

Component pages (`wiki/resources/components/`) follow a specific structure for consistency.

**Template:** See `docs/templates/template-component.md` for full template with placeholders.

**Section order:**
1. **Frontmatter + Title + Brief Description** — Standard frontmatter, then title and one-paragraph description
2. **Pillar** — Which platform pillar (e.g., Serving, Ingestion, Management) with brief explanation (defined in the vision if exist)
   - Optional **Use Cases** subsection with persona and feature links
3. **Capabilities** — Purpose bullets and optional details table
4. **Integration** — Architecture diagram, endpoints, upstream consumers, dependencies (Hard/Soft)
5. **Related** — Links to related pages with brief context

## Rules

1. Never modify files in `raw/`. They are immutable source material.
2. Always update `wiki/portal.md` when you create or delete a page.
3. Always append to `wiki/log.md` when you perform an operation.
4. Use `[[wikilinks]]` for all internal references. Never use raw file paths in page content.
5. Every wiki page must have YAML frontmatter with tags, sources, created, and updated fields.
6. When new information contradicts existing wiki content, update the wiki page and note the contradiction with both sources cited.
7. Keep source summary pages factual. Save interpretation and synthesis for concept and synthesis pages.
8. When asked a question, search the wiki first. Only go to raw sources if the wiki doesn't have the answer.
9. Prefer updating existing pages over creating new ones. Only create a new page when the topic is distinct enough to warrant it.
10. Keep `wiki/portal.md` concise — one line per page, under 120 characters per entry.

## Zettelkasten Management

The wiki follows Zettelkasten principles for persistent knowledge management. These rules ensure the knowledge base compounds over time.

### Identity

Every wiki page has a **stable unique identifier**.

- **Time-based ID** is the preferred model: `202608120746` (YYYYMMDDHHMM)
- The ID appears in frontmatter, not necessarily the filename
- The filename can change; the ID must not
- IDs enable stable references even when titles evolve

### Atomicity

Each page should represent **one meaningful knowledge building block**.

- Avoid "everything about X" pages
- Split broad topics into atomic concepts
- Atomicity is a guiding principle, not a rigid law
- Some pages (structure notes, MOCs) intentionally aggregate

### Connections

Knowledge value comes from **relationships**, not isolated notes.

- Every new page should link to at least one existing page
- State **why** the connection exists, not just that it exists
- Bad: `See also: [[Kafka]]`
- Good: `Kafka provides exactly-once delivery guarantees needed for [[idempotency]]`

### Status Lifecycle

Every concept page has a `status:` in frontmatter:

```text
draft → used → reliable
```

| Status | Criteria | Meaning |
|--------|----------|---------|
| `draft` | New or substantially changed | Insufficient validation |
| `used` | Referenced in ≥3 outputs | Practically useful |
| `reliable` | Used >8 times without major correction | Validated knowledge |

The status is **evidence-based** — track `referenced-to:` in frontmatter.

### referenced-to

Track where concepts are actually used:

```yaml
referenced-to:
  - "[[spec-product-requirements]]"
  - "[[spec-workflow-model]]"
```

This is distinct from conceptual links:
- `[[Concept]]` = these are related
- `referenced-to` = this concept contributed to producing this artifact

### Structure Notes (MOCs)

Structure notes organize other pages:

- **wiki/portal.md** — master entry point
- **wiki/specs/*.md** (03+) — specification MOCs
- Category-level navigation hubs

Structure notes can have:
- Hierarchical structures (nested lists)
- Sequential structures (argument chains: a → b → c)
- Cross-category connections (semilattice structure)

### Contradiction Handling

When new information contradicts existing knowledge:

1. Note the contradiction explicitly
2. Cite both sources
3. If resolution is clear: update the page
4. If resolution is unclear: create a `wiki/synthesis/` page analyzing the conflict
5. Consider risk-based branching for significant contradictions

### Staleness Detection

During lint passes, check for:

- Pages with `status: reliable` that required major corrections
- Pages with `status: draft` that have been used many times
- Old sources superseded by newer information
- Orphan pages with no inbound links
- Important topics mentioned but lacking their own page

### Knowledge Hygiene

- **Provenance**: every concept should trace back to `wiki/sources/` → `raw/`
- **Deduplication**: before creating a new page, search for existing coverage
- **Refactoring**: split pages that have grown beyond atomicity
- **Deprecation**: mark obsolete pages rather than deleting (maintain history)

### Git as Memory

Every wiki mutation is a Git commit:

- Commits provide the authoritative history
- Branches isolate risky changes
- Diffs show exactly what changed
- The wiki is software-independent (plain Markdown)

Commit messages should include:
- Operation type: `ingest`, `update`, `lint`, `synthesis`
- Affected pages
- Source reference if applicable
