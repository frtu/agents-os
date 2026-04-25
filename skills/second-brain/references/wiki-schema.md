# Wiki Schema

Canonical rules for LLM-maintained knowledge base wikis. This is the single source of truth — agent config templates pull from this document.

## Architecture

Three directories, three roles:

- **raw/** — immutable source documents. The LLM reads from here but NEVER modifies these files.
- **wiki/** — the LLM's workspace. Create, update, and maintain all files here.
- **output/** — reports, query results, and generated artifacts go here.

### Raw subdirectories

- `raw/assets/` — images, audio or any resources that doesn't processing but can be used inside Markdown document using syntax `![[resource/path]]`
- `raw/clippings/` — web articles captured with Obsidian Web Clipper or copied manually
- `raw/docs/` — PDFs, papers, received files, reference documents
- `raw/notes/` — handwritten notes, briefs, random ideas

### Wiki subdirectories

- `wiki/sources/` — one summary page per ingested source
- `wiki/synthesis/` — comparisons, analyses, cross-cutting themes
- `wiki/projects/` — time-bounded development work (initiatives, products, specific projects)

**Projects** — all content related to time-bounded development work:
- `wiki/projects/{initiative-name}/` — transversal initiatives (e.g., kafka-migration, sso-enforcement)
- `wiki/projects/{product-name}/` — product or platform
- `wiki/projects/{product-name}/{project-name}/` — specific project to create or extend product capabilities

**People** — all content related to team members and their processes. **See `people-ingest` skill's `references/people-schema.md` for detailed people page formats.**
- `wiki/people/processes/` — step of actions to achieve an outcome (e.g., software engineering, regulatory audit)
- `wiki/people/steps/` — a particular step of a process, a particular action to a particular system (e.g., development, deployment)
- `wiki/people/roles/` — career ladder roles with levels and tracks (e.g., role-ic-3, role-mgmt-2)
- `wiki/people/competencies/` — hard or soft skills needed to achieve a step of a process (e.g., system design, leadership). Includes category pages and individual skill pages with depth progression tables.
- `wiki/people/members/` — individual persons from a squad/team (e.g., fred)

**Product** — all content related to a product or part of the product this workspace is developing. Anything NOT developed by the team should be stored in `wiki/resources/tools`:
- `wiki/product/persona/` — categories of users with similar background & skills (e.g., product-manager, developer)
- `wiki/product/entities/` — product entities, models or logical concepts (e.g., user, account)
- `wiki/product/features/` — product-level capabilities or value propositions, including legacy/deprecated features (e.g., create user, delete account)

**Resources** — all content related to resources:
- `wiki/resources/artifacts/` — things produced by the system or more physical concepts (e.g., source code, binary package, pipeline)
- `wiki/resources/components/` — internal system components that deliver value to users, including UI components (e.g., service-a,  observability)
- `wiki/resources/dependencies/` — dependencies our application depends on (e.g., PVC, Pod, Schema registry)
- `wiki/resources/tools/` — runnable systems human/AI can reuse out of the box (e.g., JIRA, bash commands, Google Docs)

**Concepts** — all content related to concepts:
- `wiki/concepts/patterns/` — development patterns (e.g., idempotency, dead letter queue, reliability, canary deployment)
- `wiki/concepts/technologies/` — reusable technology (e.g., MCP, database, Kafka, RAG)

Always search the most specific subfolders to write into, or fallback to parent folder when not found.

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

### Ingest (processing a new source)

When the user adds a file to raw/ and asks you to process it:

1. Read the source completely
2. Discuss key takeaways with the user
3. Create a source summary page in `wiki/sources/` with: title, source metadata, key claims, and a structured summary
4. Extract and categorize content into the appropriate wiki subdirectories:
   - **Product content**: features, personas, product resources → `wiki/product/`
   - **People content**: processes, steps, competencies, members → `wiki/people/`
   - **Conceptual content**: patterns, technologies → `wiki/concepts/`
   - **Resource content**: artifacts, components, dependencies, tools → `wiki/resources/`
5. For each topic identified:
   - If a wiki page exists: update it with new information from this source, noting the source
   - If no wiki page exists: create one in the appropriate subdirectory
6. Add `[[wikilinks]]` between all related pages
7. Update `wiki/portal.md` with any new pages
8. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | Source Title`

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
- **Product**: Persona, Entities, Features
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
- Persona pages: `wiki/product/persona/developer.md` → `# Developer`
- Entity pages: `wiki/product/entities/user.md` → `# User`
- Feature pages: `wiki/product/features/create-user.md` → `# Create User`
- Process pages: `wiki/people/processes/software-engineering.md` → `# Software Engineering`
- Step pages: `wiki/people/steps/deployment.md` → `# Deployment`
- Competency pages: `wiki/people/competencies/system-design.md` → `# System Design`
- Role pages: `wiki/people/roles/role-<track>-<level>.md` → `# <Level> — <Title>` (e.g., `role-ic-3.md` → `# Senior Software Engineer`, `role-mgmt-2.md` → `# Engineering Manager`)
- Member pages: `wiki/people/members/fred.md` → `# Fred`
- Pattern pages: `wiki/concepts/patterns/idempotency.md` → `# Idempotency`
- Technology pages: `wiki/concepts/technologies/kafka.md` → `# Kafka`
- Artifact pages: `wiki/resources/artifacts/binary-package.md` → `# Binary Package`
- Component pages: `wiki/resources/components/service-a.md` → `# Service A` (see Component Page Structure below)
- Dependency pages: `wiki/resources/dependencies/schema-registry.md` → `# Schema Registry`
- Tool pages: `wiki/resources/tools/jira.md` → `# JIRA`

When creating `[[wikilinks]]`:

- **Single word**: use short form `[[Word]]` — e.g., `[[Kafka]]`, `[[JIRA]]`
- **Multiple words**: use long form `[[file-link|Display Text]]` — e.g., `[[create-user|Create User]]`, `[[30-minute-development-cycle|30-Minute Development Cycle]]`
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

### Full Component Pages

For components where this vault documents **all aspects** (capabilities + infrastructure):

**Section order:**
1. **Frontmatter + Title + Brief Description** — Standard frontmatter, then title and one-paragraph description
2. **Pillar** — Which platform pillar (e.g., Serving, Ingestion, Management, ...) with brief explanation (defined in the vision if exist)
   - Optional **Use Cases** subsection: primary persona with `[[persona-name|Persona Name]]` and bullet points of use cases with `[[feature-name|Feature Name]]`
3. **Capabilities**
   - **Purpose** — bullet points of what it does
   - Optional **Details** — capability table with descriptions
4. **Integration** — How component connects to others
   - Architecture diagram (ASCII or Mermaid)
   - Optional **Endpoints** — API endpoints if applicable
   - Optional **Upstream** — who calls this component
   - Optional **Dependencies** — table with Component, Purpose, and Dependency type (Hard/Soft)
5. **Related** — Links to related pages with brief context

**Example:**

    ---
    Category: wiki
    Tags: [component, repository, api]
    Source links: [...]
    Created: YYYY-MM-DD
    Last Updated: YYYY-MM-DD
    ---

    # Domain Service

    Backend service providing service endpoints for domain teams.

    ## Pillar

    **Serving** — used by real end users managing `User`.

    ### Use Cases

    Primary audience persona: [[end-users|End Users]]

    Used for:
    - ID lookups
    - Find user by first name

    ## Capabilities

    ### Purpose

    - Return structured results

    ### Details

    | Capability | Description |
    |------------|-------------|
    | ID Lookup | Direct dataset retrieval |

    ## Integration

    ```
    ┌──────────┐     ┌────────────┐     ┌──────────────┐
    │ WebApps  │────▶│User   Svc  │────▶│PostgreSQL    │
    └──────────┘     └────────────┘     └──────────────┘
    ```

    ### Endpoints

    Protected by [[rate-limiting|Rate Limiting]]:
    - `/users`
    
    ### Dependencies

    | Component | Purpose | Dependency |
    |-----------|---------|------------|
    | [[PostgreSQL]] | Storage | **Hard** |

    ## Related

    - [[Feature]] — powers this feature

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
