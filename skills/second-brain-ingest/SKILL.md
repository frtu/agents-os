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

Process raw source documents into structured, interlinked, **atomic** wiki pages.

## Identify Sources to Process

Determine which files need ingestion:

1. If the user specifies a file or files, use those
2. If the user says "process new sources" or similar, detect unprocessed files:
   - List all files in `raw/` (excluding `raw/assets/`)
   - Read `wiki/log.md` and extract all previously ingested source filenames from `ingest` entries
   - Any file in `raw/` not listed in the log is unprocessed
3. If no unprocessed files are found, tell the user

## Before Processing: Read Foundations

**IMPORTANT**: Before ingesting anything, read three foundation documents:

1. `docs/wiki-schema.md` — atomicity principles, PTCA decomposition (Pattern → Technology → Component → Artifact), atomic page structures, generic-vs-specific co-location rules
2. `docs/wiki-architecture.md` (or vault-specific equivalent in `{vault}/docs/wiki-architecture.md`) — category articulation, decision flowchart, ambiguous case resolution
3. The vault's `CLAUDE.md` — **the target system** the vault serves

Use the schema for *how* to decompose, the architecture for *where* to place pages, and the CLAUDE.md for *what* is relevant.

## Step 0: Identify the Target System

Before reading any source, determine the **target system** the vault represents:

- Read `{vault}/CLAUDE.md` — the top section (often quoted) names the purpose
- Vault-level target system: the whole vault represents one system (e.g., `engineering-department` → team management; `immobilier` → real estate investments)
- Product-level target system: a sub-system inside a multi-product vault (e.g., `user` → user product)

Write down (mentally or in chat) what the target system is, in one sentence. All decomposition decisions should serve it.

If the source describes something orthogonal to the target system, surface this to the user before ingesting.

## Process Each Source

For each source file, follow this workflow:

### 1. Read the source completely

Read the entire file. If the file contains image references, note them — read the images separately if they contain important information.

### 2. Present brief summary and gather context (for single clipping documents)

**For single web clipping files from `raw/clippings/`:**

Before writing anything, present:
- **Brief summary** (2-3 sentences) of what the document covers
- **Relevance check**: Ask if this is relevant to the vault's target system
- **Enrichment opportunity**: Ask if any additional tags, categories, or context should be added

Example prompt:
> "I read [filename]. Brief summary: [2-3 sentence summary].
>
> Target system for this vault: [one-line target system description].
>
> Is this relevant? Should I add any specific tags or context to enrich this document before processing?"

Wait for user response before proceeding.

**For other source types** (docs, notes, or multiple files):
Share the 3-5 most important takeaways from the source. Ask the user if they want to emphasize any particular aspects or skip any topics. Wait for confirmation before proceeding.

### 3. Decompose into atomic units (PTCA)

Before writing pages, **list the atomic units** the source covers along the four PTCA layers. This is the most important step — it determines page count and structure.

| Layer          | Directory                | Question to ask                                              |
| -------------- | ------------------------ | ------------------------------------------------------------ |
| **Pattern**    | `concepts/patterns/`     | What abstract reusable approach does this describe?          |
| **Technology** | `concepts/technologies/` | What capability or methodology is invoked (system-agnostic)? |
| **Component**  | `resources/components/`  | What system module of the target system does this build?     |
| **Artifact**   | `resources/artifacts/`   | What concrete deliverable is produced or consumed?           |

For each atomic unit:
- Check if a page already exists (use Grep / Glob in `wiki/`)
- If yes → update; if no → create
- **One concept = one page**. If two siblings appear in the source (e.g., RBAC and ABAC), they each get their own page

**Apply the generic + specific co-location rule**: when a source describes a generic concept AND one concrete implementation example, put both on the same page. Lead with the generic, follow with an "Implementation: {X}" section. Promote the specific to its own page only when it grows beyond a section or is referenced from many places.

**Case study to imitate**: the Access Control Systems / OPA source produced:
- 2 patterns: `rbac.md`, `abac.md` (siblings, each atomic)
- 1 technology: `iam.md` (generic + "Implementation: AWS IAM" section)
- 1 component: `access-control-system.md` (composite, references patterns + technology + artifact)
- 1 artifact: `policy.md` (concrete deliverable evaluated by the component)
- 1 source: `source-access-control-systems.md`

Surface your PTCA plan to the user before writing pages, so they can confirm or adjust.

### 4. Create source summary page

Create a new file in `wiki/sources/` named `source-{slug}.md`. Source summaries are **factual only** — no interpretation. The summary lists which atomic units the source produced/updated.

### 5. Create or update wiki pages (one per atomic unit)

For each atomic unit identified in step 3:

**If a wiki page already exists:**
- Read the existing page
- Add new information from this source
- Add the source to the `Source links:` frontmatter list
- Update the `Last Updated:` date
- Note any contradictions, citing both sources

**If no wiki page exists:**
- Create a new page in the most specific appropriate subdirectory
- Use the atomic page structure from `docs/wiki-schema.md` (Pattern / Technology / Component / Artifact templates)
- Include YAML frontmatter with tags, source links, created and updated dates
- Write a focused, atomic page — one concept only

**Categorization reminder**: Use the decision flowchart in `docs/wiki-architecture.md` (or vault-specific):

1. Theoretical/reusable domain knowledge? → `concepts/`
2. Definition of what we want to do? → `product/`
3. Who does it or how to do it? → `people/`
4. Something produced or used? → `resources/`
5. Concrete time-bounded work? → `projects/`

**Category guide** (across vaults):

- `wiki/concepts/patterns/` — abstract reusable approaches (rbac, abac, idempotency, feedback-loops)
- `wiki/concepts/technologies/` — capabilities/methodologies system-agnostic (iam, okr)
- `wiki/product/entities/` — business objects (account, property, lease)
- `wiki/product/features/` — functional capabilities (hiring, performance-review)
- `wiki/product/persona/` — role categories (engineering-manager, beginner-investor) — NOT individuals
- `wiki/people/processes/` — workflows (hiring-process, property-acquisition)
- `wiki/people/steps/` — granular actions (`step-{process}-{number}-{name}.md`)
- `wiki/people/competencies/` — hard or soft skills (system-design, negotiation)
- `wiki/people/roles/` — career ladder (`role-<track>-<level>.md`)
- `wiki/people/members/` — named individuals (fred, alice) — NOT role categories
- `wiki/resources/artifacts/` — deliverables (policy, performance-review-document, financing-plan)
- `wiki/resources/components/` — internal systems of the target system (access-control-system, yield-calculator)
- `wiki/resources/dependencies/` — external systems we depend on (bank, hr-system)
- `wiki/resources/tools/` — ready-to-use applications (jira, seloger)

For career ladder, competency, and process sources, prefer `/people-ingest` for specialized formats.

### 6. Add cross-links (PTCA cross-linking)

Each atomic page links across all four layers it touches:

- **Pattern** page links to: sibling patterns, technologies that implement it, components that apply it, artifacts that express it
- **Technology** page links to: patterns it implements, components that use it, artifacts it produces
- **Component** page links to: patterns it applies, technologies it uses, artifacts it produces/consumes, dependencies it relies on
- **Artifact** page links to: components that produce/consume it, patterns it expresses, technology that defines its format

Use `[[wikilink]]` for every reference. Inside tables, escape with `[[link\|Display]]`.

### 7. Update wiki/portal.md

For each new page created, add an entry under the appropriate category header:

    - [[page-name|Page Name]] — one-line summary (under 120 characters)

### 8. Update wiki/log.md

Append a structured entry:

    ## [YYYY-MM-DD] ingest | Source Title

    {One-paragraph summary.}

    **Source Processed (1):**
    - `raw/.../source.md` — short description

    **Concept Patterns Created (N):**
    - [[pattern-1]] — what it covers
    - [[pattern-2]] — what it covers

    **Concept Technologies Created (N):**
    - [[technology-1]] — what it covers

    **Components Created (N):**
    - [[component-1]] — what it covers

    **Artifacts Created (N):**
    - [[artifact-1]] — what it covers

    **Pages Updated (N):**
    - [[existing-page]] — what was added

    **Source Summary Created (1):**
    - [[source-{slug}]] — short description

    **Cross-links Added:**
    - {Notable new edges in the wikilink graph}

### 9. Report results

Tell the user what was done:
- Pages created (with links and their category — grouped by PTCA layer)
- Pages updated (with what changed)
- Any contradictions found with existing content
- Whether the atomic decomposition fully covered the source

### 10. Stage changes (do not commit unless asked)

Call `/capture-changes-git` to stage all changes and create the change log entry:

```
/capture-changes-git
  trigger: {user's original instruction that started this ingest}
  operation: ingest
  subject: {source-name}
  input_files: {all raw/ files processed}
  created_files: {all new wiki pages created}
  updated_files: {all existing pages updated + portal.md + log.md}
```

This will:
1. Stage all input sources and produced wiki pages
2. Append a structured change context block to the log entry
3. Verify only intended files are staged

Do not commit unless the user explicitly asks.

## Categorization Best Practices

**ALWAYS consult `docs/wiki-architecture.md` when uncertain**. Common pitfalls:

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
- **Artifact** (in `resources/artifacts/`): Output produced (e.g., performance-review-document, financing-plan, policy)

### Technology vs Dependency vs Tool
- **Technology** (in `concepts/technologies/`): Abstract capability (e.g., kafka, land-registry)
- **Dependency** (in `resources/dependencies/`): Concrete system we depend on (e.g., kafka-cluster, hr-system, bank)
- **Tool** (in `resources/tools/`): Usable interface (e.g., kafka-cli, workday, seloger)

### Pattern vs Technology
- **Pattern** (in `concepts/patterns/`): An abstract reusable *approach* (rbac, abac, idempotency, feedback-loops)
- **Technology** (in `concepts/technologies/`): A *capability* or *system class* (iam, okr, career-ladder)
- A pattern answers "what approach"; a technology answers "what kind of system / methodology"

### Component vs Technology
- **Component** belongs to the **target system** of the vault — something the vault's owners build/operate
- **Technology** is **system-agnostic** — exists independent of any specific vault
- E.g., for engineering-department: `iam` is a technology (concept), `access-control-system` is a component of the team's security stack

## Atomicity Rules

1. **One concept per page.** Two siblings in a source → two pages. RBAC and ABAC are separate, not "Access Control Models".
2. **Generic + specific co-location.** A generic concept and its first concrete example stay on the same page (e.g., `iam.md` includes "Implementation: AWS IAM"). Promote to a separate page only when the specific grows substantially.
3. **PTCA cross-linking.** Every component links to the patterns it applies, technologies it uses, and artifacts it produces/consumes.
4. **Atomicity test before writing.** "Can someone unfamiliar with this domain understand this page on its own, with only short hops via wikilinks?" If no, split or co-locate appropriately.

## Conventions

- Source summary pages are **factual only**. Save interpretation and synthesis for concept and synthesis pages.
- Wiki pages should be **factual**. Focus on what the source says about the topic.
- A single source typically touches **5-15 wiki pages** along the PTCA layers. This is normal.
- When new information contradicts existing wiki content, **update the wiki page and note the contradiction** with both sources cited.
- **Prefer updating existing pages** over creating new ones. Only create a new page when the topic is a distinct atomic unit.
- **Always use the most specific subfolder** when creating pages.
- Use `[[wikilinks]]` for all internal references. Never use raw file paths.
- **Inside tables**, escape `|` in wikilinks: `[[page-name\|Display Text]]` to avoid collision with table column separators.
- **Component pages must follow the Component Page Structure** in `second-brain` skills `references/wiki-schema.md` exactly.

## What's Next

After ingesting sources, the user can:
- **Ask questions** with `/second-brain-query` to explore what was ingested
- **Ingest more sources** — clip another article and run `/second-brain-ingest` again
- **Health-check** with `/second-brain-lint` after every 10 ingests to catch gaps and atomicity violations
