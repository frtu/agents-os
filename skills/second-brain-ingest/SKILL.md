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

## Efficiency: Inventory First, Then Scale the Read

Three moves — learned from large ranking-source ingests — make a run dramatically faster and cut duplicate pages. Do them before decomposing.

### A. Build the existing-concept inventory ONCE, up front

Before reading sources, snapshot what already exists so every later decision is create-vs-**update** with full context:

```bash
ls wiki/concepts/patterns/**/*.md wiki/concepts/technologies/**/*.md 2>/dev/null
grep -nE "^- \[\[" wiki/portal.md   # existing pages + one-line summaries
```

Keep this list. It is (1) the dedup filter for step 3, and (2) the "already covered — do not re-report" brief you hand to sub-agents. Most duplicate pages come from skipping this.

### B. Fan out sub-agents for large or multiple sources (when available)

A source over ~1,500 lines / ~50KB (or several sources at once) should **not** be read into the main context. Launch one `general-purpose` sub-agent per source, in parallel, to **read and extract only** — the main agent stays the sole writer (keeps cross-linking and naming consistent).

Brief each agent with: the extraction goal · **the existing-concept inventory from A** (so it flags only genuinely new units) · a request for a **bounded report (<~800 words) with short traceable quotes**. Then trust-but-verify the report against the raw source for anything you'll assert as fact.

This protects context, parallelizes the slow reads, and is the intended reading of any "fan out sub agents" instruction.

**Two sub-agent roles — keep them distinct:**

1. **Read-only inventory/extraction agents** — read a source (or a target vault's existing pages) and report back. They never write. Use them to parallelize slow reads and to snapshot a vault you're about to enrich.
2. **A dedicated writer agent for an *independent* vault.** When an ingest spans two vaults (see section D), the writer for the **primary** vault is always the **main agent** (it owns cross-linking + naming). A **second, self-contained** vault (e.g. `security`) may be handed to one background writer sub-agent with a complete brief, because its pages don't cross-link back into the primary vault's fresh pages. Verify that writer's output afterward (read the files it claims to have changed).

Never fan out multiple writers into the **same** vault in parallel — concurrent writers produce inconsistent slugs and duplicate pages.

### C. Honor a scoped ingest

If the user scopes the request to a subset of PTCA (e.g. "**generic concepts only**", "just the patterns", "capabilities not projects"), create only those layers and skip the rest — state the scope back so it's explicit. Don't force a full PTCA decomposition onto a deliberately narrow ask.

### D. Split capability knowledge from infrastructure specifics (multi-vault)

A single source often mixes two kinds of content that belong in **different vaults**:

| Content kind                                                                                                       | Goes to                                     | Page shape                       |
| ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------- | -------------------------------- |
| **Conceptual / behavioral** — what a capability does, its patterns, processes, steps, failure modes, roles         | the **capability vault** (e.g. `product-a`) | normal PTCA pages                |
| **Environment-specific** — URLs, region lists, cluster specs, image versions, API endpoints, repo names, git paths | the **infra vault** (`infra`)               | `infra-{product}-{component}.md` |

The rule of thumb: **anything that changes when you redeploy or move regions** (a URL, a version pin, a region code, an endpoint) is infra and belongs in `infra`. Anything that stays true regardless of environment (a pattern, a data flow, a role) is capability knowledge and stays in the capability vault.
- Keep the capability vault **environment-free**. Do not paste URLs, versions, or region tables into `product-a` pages — let the infra page reference back instead.
- Enrich (append to) an existing `infra-{product}-{component}.md` rather than creating a duplicate; refresh its `Last Updated`.
- If the user names the target vaults explicitly ("do NOT ingest URLs into `product-a`, append them to `infra`"), honor that split exactly and state it back.
- Use the **read-only inventory + independent-vault writer** sub-agent pattern from section B for the infra vault.

**Cross-vault link convention:** reference a page in another vault with the full-path form `[[Vault/xxx/wiki/resources/tools/xxx|Xxx]]`. A cross-vault link that dangles (target not yet created in the other vault) is acceptable — do not let the `MISSING` check in step 6 block on cross-vault targets; only enforce resolution for **same-vault** links.

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

**Verify content matches the filename.** Files are often mis-named or mis-filed (e.g. a "Orchestration-Plan" file that is actually an API-review meeting transcript). If the actual content is off-topic relative to the ingest goal or the folder it sits in, surface it to the user and exclude it rather than forcing its content into unrelated pages. Ingest by *what the file says*, not what it is named.

**Reuse an existing source page.** Before creating a `source-{slug}.md`, grep `wiki/sources/` — a supplemental or re-ingest of an already-summarized source should **update** the existing source page (add new `Source links` targets, refresh `Last Updated`), not create a duplicate.

**Detect a duplicate source before decomposing.** Beyond filename, check whether the *content* is one you have already ingested (the same recording re-exported, the same doc re-shared under a new name). If it is identical or near-identical, do **not** re-assert its claims into pages — add a short "duplicate of [[source-…]]" note to the existing source page and ingest only the genuinely new delta, if any. (Example: the canary-deployment Zoom recording ingested twice — the second was captured as a duplicate note, not duplicated claims.)

### 1b. Resolve entity names before writing any link

**If the source is an auto-generated transcript (Whisper/Zoom/...), run `/lint-transcript-normalise` on it FIRST** — that pre-skill fixes garbled proper nouns against its correction dictionary and produces an "Entities to confirm" list. Do not start decomposition until the transcript is normalised and the ambiguous mentions are confirmed.

Whatever the source, before you write **any** `[[wikilink]]` for a person, product, or system:

1. **Resolve against what exists.** Grep  `wiki/**/members/`, `raw/People/**`, and `wiki/portal.md`, and reuse the entity's **exact** slug + display form. Never invent a slug when an entity already exists under a different name.
2. **Cross-check roles, don't infer them.** "User service deals with Paul" does not mean Paul is on the User team. Only state a person's team/role if the source or an existing wiki page says so.
3. **Don't trust speaker labels.** Transcripts often collapse every line to one speaker — do not assert who said what; attribute to the meeting or participants collectively.
4. **Carry forward the "Entities to confirm" list** from `/lint-transcript-normalise` (plus anything else you could not resolve) and confirm it with the user in step 2 before committing. Write confirmed forms; leave unresolved ones as plain text rather than guessing.

Do not silently promote a transcription artifact into a wikilink. A wrong `[[name]]` is worse than an unlinked plain-text mention flagged for review. See `.claude/commands/lint-transcript-normalise/SKILL.md` for the full failure-mode reference and dictionary schema.

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
Share the 3-5 most important takeaways from the source. Ask the user if they want to emphasize any particular aspects or skip any topics. If the source is a transcript, also present the **"Entities to confirm"** list from step 1b (garbled names, lone initials, unresolved people/products, uncertain roles) and ask the user to confirm or correct them. Wait for confirmation before proceeding.

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

**Recognize end-to-end flows → Process + Steps.** PTCA captures the *nouns*; a source that describes an **end-to-end flow** (a lifecycle, a pipeline, "how data gets from A to B", a build-and-deploy sequence) also has *verbs* that belong in the people layer:
- The whole flow → one `people/processes/{name}.md` page (overview table of the ordered stages, plus any cross-cutting split such as Control Plane vs Data Plane, a change-detection/trigger table, and a Roles table).
- Each stage → one `people/steps/step-{process}-{n}-{name}.md` page, chained with **prev/next** links, each linking up to the parent process and out to the concepts (patterns/technologies/components) it exercises.

Do this in addition to the PTCA nouns, not instead of them — the Data Movement source produced both a `data-processing` process with 6 steps **and** component/dependency/tool pages.

**Fan out one source by concern.** A single product/design doc usually mixes three concerns that belong on three different page types — do not dump them all onto one page:
- **Product / vision / problem-space / objectives** → the `product/` feature page. Keep this page product-only (no architecture, no tech stack, no workflow).
- **Architecture / topology / technology stack / dev environment / integration position** → a consolidated `resources/components/` page for the target system's module.
- **Workflow / lifecycle / operations** → the `people/processes/` page and its `people/steps/` pages.

The product page was split exactly this way: product info → `pillar-1` feature, architecture/tech-stack/dev-env → `pillar-1-components`, developer workflow/lifecycle/operations → `pillar-1-process` process + steps.

**Custom vs standard artifacts.** Only give an artifact its own `resources/artifacts/` page when it is **custom to the target system**. An artifact that is a **standard deliverable of an external technology** (e.g. Kafkaß's `partition`, `consumer-group`, ...) is referenced/attributed to that technology — not duplicated as its own page. When a custom artifact is composed of several concrete files, that is **one artifact page** whose Structure table lists each file, its role, and the step that produces it (e.g. `dsl.md` = `DslDefinition` class + `application.<DslName>.yaml`).

**Generic pattern vs concrete artifact.** A reusable, system-agnostic model goes to `concepts/patterns/` (e.g. `event-driven-architecture`); the concrete platform instance that implements it goes to `resources/artifacts/` (e.g. `orchestration-flow`). The artifact links to the pattern as "implements"; the pattern links to the artifact as "implemented by".

**Steps declare Input → Output.** Every `people/steps/` page uses explicit `## Input`, `## Action`, `## Output` sections. Chain the steps so each step's Output feeds the next step's Input, and the composed outputs build the artifact the process produces (steps 1–3 of `data-processing` compose the `dag` artifact; 4–6 build, run, observe it).

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
- **Check for a folder `README.md` describing theme subfolders.** Some directories (e.g. `wiki/resources/artifacts/README.md`) split their contents into theme subfolders and carry a routing table. Before writing, read that README and place the page in the matching theme subfolder — never drop it at the folder root when a theme fits. If no theme fits, follow the README's fallback instruction (typically: propose a new theme folder rather than defaulting to root).
- Use the atomic page structure from `docs/wiki-schema.md` (Pattern / Technology / Component / Artifact templates)
- Include YAML frontmatter with tags, source links, created and updated dates
- Write a focused, atomic page — one concept only

**If the source describes an undecided decision** (options weighed, nothing chosen — e.g. "we could either… or…", "still investigating", a phased/deferred build-out), capture it as a **DRAFT option page**, not as a settled design. Set `Status: DRAFT — still investigating` in frontmatter, give it an **options table** (option · mechanism · pros · cons · referenced concepts) and an **Open Sub-Decisions** list, and link out to the atomic concept pages instead of restating them. See Decomposition Rule 6 + the DRAFT template in `docs/wiki-schema.md`. Never write a DRAFT decision as if one option won.

**If the source describes a decision that WAS made** (options weighed, one chosen — a build-vs-borrow call, a picked engine/language), capture it as an **ADR-style synthesis page** in `wiki/synthesis/`: decision · context · chosen option · rejected alternatives · consequences. ADR = decided (reasoning preserved); DRAFT = still open. Examples: `dsl-build-vs-borrow`, the workflow definition investigation.

**Tag content maturity to avoid overstating commitment.** When a source describes proposed-but-not-committed work or phased scope, tag it (MVP / v1.5 / v2 / proposed) rather than writing it as shipped. Scaffolding that is aspirational must read as aspirational.

**Flag uncertain content as Caveats.** Reconstructed field/config names, metrics that disagree across sources, single-customer or single-source generalizations, and unverified numbers get a `> **Caveat:**` note (or a Caveats section) stating what is uncertain and why — never silently promoted to fact. (Example: reconstructed ranking config field names were flagged as such.)

**Don't duplicate a section that already exists.** If an existing page already covers a sub-topic well (e.g. security methodology living in `policy-enforcement.md`), reference that page/section rather than creating an overlapping page. Integrate and evolve; don't append a parallel section.

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

**Categorization tie-breakers (the chronic miscategorization).** The artifact ↔ component ↔ pattern ↔ feature boundary is where pages get mis-filed and later relocated. Before filing, apply this test:
- **Runs or gets imported** (SDK, service, engine, UI module) → **component** (`resources/components/`). An SDK is a component even though it ships as a library.
- **Abstract, reusable model** independent of any vault (topology, algorithm, design pattern) → **pattern** (`concepts/patterns/`).
- **Concrete file produced/consumed** at build/runtime (config, policy, generated doc) → **artifact** (`resources/artifacts/`).
- **User-facing capability or value proposition** → **feature** (`product/.../features/`), **regardless of lifecycle** — a legacy/deprecated capability is still a feature, not a component.

When torn between artifact and pattern, keep both and link them (concrete instance in artifacts references the abstract model in patterns).

### 6. Add cross-links (PTCA cross-linking)

Each atomic page links across all four layers it touches:

- **Pattern** page links to: sibling patterns, technologies that implement it, components that apply it, artifacts that express it
- **Technology** page links to: patterns it implements, components that use it, artifacts it produces
- **Component** page links to: patterns it applies, technologies it uses, artifacts it produces/consumes, dependencies it relies on
- **Artifact** page links to: components that produce/consume it, patterns it expresses, technology that defines its format

Use `[[wikilink]]` for every reference. Inside tables, escape with `[[link\|Display]]`.

**Verify every new link resolves.** Broken wikilinks are the most common post-ingest defect and are cheap to catch. Batch-check that each target file exists before finishing:

```bash
for l in <slug-1> <slug-2> ...; do find wiki -name "$l.md" | grep -q . || echo "MISSING: $l"; done
```

Fix any `MISSING` (wrong slug, or a page you meant to create but didn't) before step 7.

**Cross-vault links are exempt.** The check above is for **same-vault** links only. A full-path link into another vault (`[[Vault/xxx/wiki/resources/components/yyy|…]]`) may legitimately dangle — do not treat it as `MISSING`, and do not create a placeholder in this vault to satisfy it.

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

Call `/change-management-1-stage` to stage all changes and create the change log entry:

```
/change-management-1-stage
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
- **Never write a `[[wikilink]]` for a name you have not resolved** against people or members name in portal (see step 1b). Transcripts mangle proper nouns; confirm garbled names, lone initials, and inferred roles with the user before committing them.
- Wiki pages should be **factual**. Focus on what the source says about the topic.
- A single source typically touches **5-15 wiki pages** along the PTCA layers. This is normal.
- When new information contradicts existing wiki content, **update the wiki page and note the contradiction** with both sources cited.
- **Prefer updating existing pages** over creating new ones. Only create a new page when the topic is a distinct atomic unit.
- **Always use the most specific subfolder** when creating pages. If the destination folder has a `README.md` with a theme-routing table (e.g. `wiki/resources/artifacts/README.md`), read it and file the page in the matching theme subfolder.
- Use `[[wikilinks]]` for all internal references. Never use raw file paths.
- **Inside tables**, escape `|` in wikilinks: `[[page-name\|Display Text]]` to avoid collision with table column separators.
- **Component pages must follow the Component Page Structure** in `second-brain` skills `references/wiki-schema.md` exactly.

## What's Next

After ingesting sources, the user can:
- **Ask questions** with `/second-brain-query` to explore what was ingested
- **Ingest more sources** — clip another article and run `/second-brain-ingest` again
- **Health-check** with `/second-brain-lint` after every 10 ingests to catch gaps and atomicity violations
