# Wiki Schema

Shared schema for all knowledge base vaults.

## Architecture

Three directories, three roles:

- **raw/** — immutable source documents. The LLM reads from here but NEVER modifies these files.
- **wiki/** — LLM workspace. Create, update, and maintain wiki pages here.
- **output/** — reports, query results, and generated artifacts.

### Raw Subdirectories

- `raw/assets/` — images, audio, resources for markdown embedding (`![[resource/path]]`)
- `raw/clippings/` — web articles from Obsidian Web Clipper
- `raw/docs/` — PDFs, papers, reference documents
- `raw/notes/` — handwritten notes, briefs, ideas
- `raw/transcripts/` — video/audio transcripts, podcast notes, recorded conversations

### Common Wiki Structure

- `wiki/portal.md` or `wiki/index.md` — master catalog of wiki pages
- `wiki/log.md` — append-only chronological record
- `wiki/sources/` — one summary page per ingested source
- `wiki/synthesis/` — comparisons, analyses, cross-cutting themes

## Target System

Every vault has a **target system** — the purpose it serves. The target system is either:

- **Vault-level** — the entire vault represents one system (e.g., `engineering-department` → team management system; `immobilier` → real estate investment system)
- **Product-level** — a sub-system inside a multi-product vault (e.g., `product-a` vault → Product A product; `infra` vault → infrastructure & dependencies)

**Why this matters**: All decomposition decisions should serve the target system. A page only belongs in the wiki if it advances understanding of, or capability within, the target system.

**Identify the target system first** before ingesting any source. Read the vault's `CLAUDE.md` — the top section (often quoted) names the purpose. If the source describes something orthogonal to the target system, flag it before ingesting.

Examples:
- `engineering-department/CLAUDE.md` → "Shape the team from/to the env such that they succeed"
- `product-a/CLAUDE.md` → Product A product
- `immobilier/CLAUDE.md` → real estate investments

## Atomicity & Decomposition

A wiki page is **atomic** when it covers exactly one unit of knowledge — one pattern, one technology, one component, one artifact. Atomicity test:

> *Can someone unfamiliar with this domain understand this page on its own, with only short hops via wikilinks to read more?*

If a page covers two concepts that get compared, both deserve their own page; the comparison lives on each, plus optionally a synthesis page.

### The Four Atomic Layers

When ingesting a technical source, decompose along these four layers. Each layer maps to a directory:

| Layer | Directory | What it captures | Example (Access Control case study) |
|-------|-----------|------------------|--------------------------------------|
| **Pattern** | `concepts/patterns/` | Abstract reusable approach or model | `rbac`, `abac` |
| **Technology** | `concepts/technologies/` | Capability or methodology (system-agnostic) | `iam` |
| **Component** | `resources/components/` | System module that delivers value within the target system | `access-control-system` |
| **Artifact** | `resources/artifacts/` | Concrete deliverable produced or consumed | `policy` |

This is the **PTCA decomposition** (Pattern → Technology → Component → Artifact). Most technical sources can be decomposed along all four layers.

### Decomposition Rules

1. **One concept, one page.** If the source covers RBAC *and* ABAC, create one page each — never a combined "Access Control Models" page. The comparison goes in each page's "vs X" section.

2. **Atomic before composite.** Create the atomic units first (rbac, abac, iam, policy), then assemble the composite (access-control-system) that references them.

3. **Generic + specific co-location.** When a generic concept has a concrete implementation example, put both on the same page:
   - Lead with the **generic** definition and structure (top of page)
   - Follow with **Implementation: {X}** section as a concrete example
   - Example: `iam.md` contains generic IAM concepts + an "Implementation: AWS IAM" section
   - Anti-pattern: separate `iam.md` and `aws-iam.md` — fragments the knowledge

   Promote the specific to its own page only when:
   - Multiple sources discuss it
   - It has substantial details that overwhelm the generic page
   - It's already heavily cross-referenced

4. **Target-system relevance.** Every atomic page must serve the target system. If a pattern (e.g., `rbac`) only exists in the wiki to be referenced by a component (e.g., `access-control-system`) that itself serves the target system, that's fine — the chain is intact.

5. **Cross-link every layer.** Each atomic page links to its siblings up and down the stack:
   - Pattern ↔ Pattern (rbac ↔ abac comparison)
   - Pattern → Technology (rbac → iam)
   - Pattern → Component (rbac → access-control-system)
   - Pattern → Artifact (rbac → policy)
   - Component → all patterns, technologies, artifacts it uses

6. **Capture undecided decisions as DRAFT option pages — don't assert a choice.** When a source describes an approach that is still being investigated (multiple options weighed, no decision made), do **not** write the wiki as if one option won. Create the page with `Status: DRAFT — still investigating` in frontmatter and an **options table** (option · mechanism · pros · cons · which concepts it references), plus an **Open Sub-Decisions** list. Reference the atomic concept pages rather than restating them. This keeps the wiki honest about maturity and traceable back to the decision space. Minimal shape:

   ```markdown
   ---
   Category: {product/.../features | synthesis}
   Status: DRAFT — still investigating
   Tags: [draft, ...]
   Source links: [...]
   ---
   # {Decision Name} (DRAFT — Still Investigating)
   > **Status: DRAFT.** Options below are under investigation, not decided.
   ## The Open Question
   {What must be decided, and the constraint driving it.}
   ## Options
   | Option | Mechanism | Pros | Cons | References |
   ## Open Sub-Decisions
   - {sub-decision} — {leaning, if any}. *Undecided.*
   ## Reference Concepts
   - [[concept]] — relation
   ```

   **Settled trade-offs are different from DRAFT.** When a decision *has* been made after weighing options (a build-vs-borrow call, a chosen query language, a picked storage engine), record it as an **ADR-style synthesis page** in `wiki/synthesis/` — decision + context + chosen option + rejected alternatives + consequences — not a DRAFT. DRAFT = still open; ADR = decided, with the reasoning preserved. Examples from the log: `query-language-build-vs-borrow` (in-house DSL V1 vs PPL 2.0), the ClickHouse-vs-Elasticsearch investigation.

7. **Categorization tie-breakers (artifact ↔ component ↔ pattern ↔ feature).** This boundary is the most common miscategorization — `kotlin-sdk` was filed as an artifact (it is a **component**), `dag-pipeline-architecture` as an artifact (it is a **pattern**), `enterprise-search` as a component (it is a **feature**). Resolve with this test:

   | If the thing is… | It is a… | Home |
   | --- | --- | --- |
   | A runnable or importable system/library/service the target system operates (SDK, service, engine, UI module) | **Component** | `resources/components/` |
   | An abstract, reusable model/approach that exists independent of any vault (a topology, an algorithm, a design pattern) | **Pattern** | `concepts/patterns/` |
   | A concrete file/deliverable produced or consumed at runtime/build time (a config, a policy, a generated doc) | **Artifact** | `resources/artifacts/` |
   | A capability or value proposition offered to users | **Feature** | `product/.../features/` |

   - **Features are lifecycle-independent.** A legacy, deprecated, or sunset capability is still a **feature** — do not demote it to a component because it is old. "Features represent capabilities or value propositions regardless of lifecycle status."
   - **When in doubt between artifact and component:** does it *run/get imported* (component) or is it *produced/consumed as a file* (artifact)? An SDK is a component even though it ships as a library.
   - **When in doubt between artifact and pattern:** is it a *concrete instance with real filenames* (artifact) or an *abstract model* (pattern)? Keep both and link them (Rule 19).

### Atomic Page Structures

#### Pattern page (`concepts/patterns/{name}.md`)

```markdown
---
Category: concepts/patterns
Tags: [...]
Source links: [...]
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
---

# {Pattern Name}

{One-paragraph definition — what the pattern is, when it applies.}

## How It Works
{Mechanism, inputs, outputs.}

## {Pattern} vs {Sibling Pattern}
{Comparison table — only when a closely related pattern exists.}

## When to Use
{Decision guidance.}

## Implementation
{Optional concrete example, e.g., Rego/code/policy snippet.}

## Related
- [[sibling-pattern]] — relation
- [[technology]] — implementing technology
- [[component]] — component that applies this pattern
- [[artifact]] — artifact this pattern shapes
```

#### Technology page (`concepts/technologies/{name}.md`)

```markdown
---
Category: concepts/technologies
Tags: [...]
---

# {Technology Name}

{One-paragraph definition.}

## Core Capabilities
{Bullet list.}

## {Models/Variants/Approaches}
{Table if applicable.}

## Architecture
{ASCII diagram — generic.}

## Implementation: {Concrete Example}
{Lead with one concrete implementation. Lift to its own page only when warranted.}

### Key Concepts
### {Specific structure / API / model}
### Examples

## Related
- [[pattern]] — pattern this technology implements
- [[component]] — component built on this technology
- [[artifact]] — artifact this technology produces
```

#### Component page (`resources/components/{name}.md`)

Components are system modules of the **target system**. Use this template:

```markdown
---
Category: resources/components
Tags: [pillar, domain, ...]
---

# {Component Name}

{One-paragraph: what it does within the target system.}

## Pillar
{Pillar within the target system — e.g., Security, Serving, Ingestion, Management.}

### Use Cases
{Features/processes powered by this component.}

## Capabilities
### Purpose
### Details (optional table)

## Integration
{ASCII diagram showing component-in-context within target system.}

### Dependencies
{Table — hard/soft.}

## Request/Response or Operations
{Concrete interface.}

## Implementations
{Optional table mapping abstract roles to concrete systems.}

## Related
- [[pattern]] — patterns it applies
- [[technology]] — technologies it uses
- [[artifact]] — artifacts it produces/consumes
```

#### Artifact page (`resources/artifacts/{name}.md`)

Give an artifact its own page only when it is **custom to the target system**. A deliverable that is a **standard artifact of an external technology/dependency** (e.g. an Elasticsearch `index-template`, `search-template`, or `mapping`) is attributed to that technology and **referenced** — never re-modeled as if the target system defined it. If it's already a `product/.../entities/` page, link the entity. A custom artifact composed of several files (e.g. a search-platform `dag` = `DagProducer` + `application.<Dag>.yaml` + `job-dag-mapping.yaml`) is **one** page whose Structure table lists the parts and the step that produces each.

```markdown
---
Category: resources/artifacts
Tags: [...]
---

# {Artifact Name}

{One-paragraph: what kind of deliverable, who produces it, who consumes it. State "custom to {target system}" and link the generic pattern it implements.}

## Structure
{Table of elements/fields — or, for a multi-file artifact, the parts and the step that produces each.}

## Languages / Formats (if applicable)
{Table of representation choices.}

## Examples
{Concrete examples in 2-3 representative formats.}

## Lifecycle
{Author → Review → Deploy → Enforce — or analogous.}

## Patterns
{Reusable patterns for authoring or composing this artifact.}

## Related
- [[component]] — components that produce/consume it
- [[pattern]] — patterns it expresses
- [[technology]] — technology that defines its format
```

#### Step page (`people/steps/step-{process}-{n}-{name}.md`)

A step is one action in a process. Every step page **declares its Input and Output explicitly** so the chain composes: step _n_'s Input is step _n-1_'s Output, and successive step Outputs assemble into the artifact the process produces.

```markdown
---
Category: wiki
Tags: [step, ...]
Source links: [...]
---

# {Step Name}

Step {n} of [[{process}|{Process Name}]]. {One sentence: who does what.}

## Input
- {What this step consumes — the prior step's output, an SDK/tool, source data.}

## Action
- {The concrete work performed.}

## Output
- {What this step produces — names the file/artifact part it contributes.}

## Related
- [[{process}|{Process Name}]] — parent process
- [[step-{process}-{n-1}-...|Previous]] / [[step-{process}-{n+1}-...|Next]]
- [[artifact]] / [[component]] / [[pattern]] it exercises
```

### Case Study Reference

The Access Control Systems / OPA source (2026-05-31 ingest) is a canonical PTCA decomposition:

- **Patterns**: `rbac`, `abac` (siblings, each atomic)
- **Technology**: `iam` (generic + AWS IAM implementation co-located)
- **Component**: `access-control-system` (composite — references patterns, technology, artifact)
- **Artifact**: `policy` (concrete deliverable evaluated by the component)

See `wiki/log.md` under `[2026-05-31] ingest | Access Control Systems` for the full structure.

## Page Format

## Naming Conventions

- Filenames: **kebab-case** with `.md` extension
- Page titles: **Title Case**
- Wikilinks: Use page title `[[Create Index]]` or alias `[[create-index|Create Index]]`
- Wikilink escaping in tables: Use `[[link\|Display]]` to avoid collision with table `|`

## Operations

### Ingest (processing a new source)

1. **Identify the target system** for the vault (read CLAUDE.md)
2. Read the source completely
3. **Verify the source is new, not a duplicate.** Grep `wiki/sources/` and existing pages. If the source is identical or near-identical to one already ingested (e.g. the same recording re-exported, the same doc re-shared), do **not** re-assert its claims into pages — add a short "duplicate of [[source-…]]" note to the existing source page and stop. Only ingest the genuinely new delta.
4. Discuss key takeaways with the user
5. **Decompose along the PTCA layers** — list candidate patterns, technologies, components, artifacts
6. Create a source summary page in `wiki/sources/`
7. For each atomic unit: update existing page or create new one (one concept per page). **Integrate, don't duplicate** — if a sub-topic is already well covered on another page, link to that page/section instead of restating it.
8. **Flag uncertain content in a Caveats block.** Reconstructed values, numeric inconsistencies across sources, single-source/single-customer generalizations, and unverified metrics get a `> **Caveat:**` note (or a Caveats section) citing what is uncertain and why — never silently promoted to fact.
9. Add `[[wikilinks]]` between all related pages (every layer cross-links). Names you could not resolve stay **plain text**, never a wikilink (see Rule 22).
10. Update the index with any new pages
11. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | Source Title`

### Query (answering questions)

1. Read the index to find relevant pages
2. Read the relevant wiki pages
3. Synthesize an answer with `[[wikilink]]` citations
4. Offer to save valuable artifacts as new pages in `wiki/synthesis/`

### Lint (health check)

1. Scan for contradictions between pages
2. Find stale claims superseded by newer sources
3. Identify orphan pages (no inbound links)
4. Find topics mentioned but lacking their own page
5. Check for missing cross-references
6. Verify pages are in correct subdirectories
7. **Check atomicity**: flag pages that bundle two or more atomic units
8. **Check PTCA coverage**: for each component, verify links to patterns/technologies/artifacts it uses
9. Report findings and offer to fix issues
10. Log the lint pass: `## [YYYY-MM-DD] lint | Summary of findings`

## Templates

Use templates from `docs/templates/` when creating structured pages:

| Template | Use For | Key Sections |
|----------|---------|--------------|
| `template-component.md` | Internal system components (capabilities, integration) | Pillar, Capabilities, Integration, Dependencies |
| `template-infra-component.md` | Infrastructure deployment pages (topology, URLs) | Architecture, Deployment (Environments & URIs), Monitoring, Roadmap |

### Infrastructure Components (`infra-{product}-{component}`)

When creating pages in `wiki/resources/components/` for the **awx-infra** vault:

1. Use `template-infra-component.md` as the base
2. Use naming convention: `infra-{product}-{component-name}.md`
   - `{product}` — the product/domain (e.g., `search`, `ingestion`, `observability`)
   - `{component-name}` — the specific component (e.g., `service`, `facade`, `realtime`)
   - Examples: `infra-search-service.md`, `infra-search-facade.md`, `infra-ingestion-realtime.md`
3. Focus on deployment details: environments, regions, URIs, monitoring
4. Link to main component page in capability-focused vault (e.g., search vault)
5. Add Roadmap section only if active timeline exists — place it last

#### Capability-vs-infra split (which vault gets what)

A source often mixes conceptual knowledge with deployment specifics. Route each to the right vault:

| Content kind | Vault | Test |
| --- | --- | --- |
| Patterns, processes, steps, data flow, failure modes, roles | **capability** vault (e.g. `search`) | true regardless of environment |
| URLs, region lists, cluster specs, image/SDK versions, API endpoints, repo & GitOps paths | **awx-infra** vault (`infra-{product}-{component}`) | changes when you redeploy or move regions |

- Keep capability pages **environment-free** — link to the infra page rather than pasting a URL/version/region table.
- **Enrich** an existing `infra-{product}-{component}.md` (append + refresh `Last Updated`); don't duplicate.
- **Cross-vault links** use the full-path form: `[[Vault/search/wiki/resources/tools/argocd|ArgoCD]]`. A cross-vault link may dangle if the target isn't created yet — that's acceptable; enforce resolution only for **same-vault** links.
- When one ingest spans both vaults, the **main agent** writes the primary vault (owns cross-linking); a single background **writer sub-agent** may own the self-contained infra vault. Never run two writers into the same vault.

## Rules

1. Never modify files in `raw/`. They are immutable source material.
2. Always update the index when creating or deleting pages.
3. Always append to `wiki/log.md` when performing operations.
4. Use `[[wikilinks]]` for all internal references.
5. Every wiki page must have YAML frontmatter.
6. When new info contradicts existing content, update and cite both sources.
7. Keep source summaries factual. Save interpretation for synthesis pages.
8. Search the wiki first. Only go to raw sources if wiki doesn't have the answer.
9. Prefer updating existing pages over creating new ones.
10. Keep the index concise — one line per page, under 120 characters per entry.
11. Use templates from `docs/templates/` when creating structured pages.
12. **One concept per page.** If two atomic units coexist in a single source, create two pages.
13. **Generic + specific co-location.** Don't fragment a concept and its first implementation example — keep them on one page until the implementation grows enough to warrant promotion.
14. **PTCA cross-linking.** Every component links to patterns it applies, technologies it uses, and artifacts it produces/consumes.
15. **Capability-vs-infra split.** Keep environment-specific detail (URLs, versions, regions, endpoints) out of capability vaults — put it in the `awx-infra` vault's `infra-{product}-{component}` page and link across with the full-path form.
16. **End-to-end flows become Process + Steps.** A lifecycle/pipeline in a source produces one `people/processes/{name}.md` plus chained `step-{process}-{n}-{name}.md` pages, in addition to its PTCA nouns.
17. **Fan out one source by concern.** A product/platform doc splits by the *kind* of knowledge, each to its home page: product info (vision, problem, objectives, characteristics, solution, goals) → `product/.../features/{feature}.md`; architecture/topology/tech-stack/integration → `resources/components/{...}.md`; human workflow/lifecycle/operations → `people/processes/{...}.md` + steps. The feature page stays **product-only** — no architecture, no how-to.
18. **Custom vs standard artifacts.** Create a `resources/artifacts/` page only for artifacts **custom to the target system**. A **standard** artifact of an external technology/dependency (e.g. Elasticsearch `index-template`, `search-template`, `mapping`) is attributed to that technology and referenced — never duplicated as custom.
19. **Generic pattern vs concrete artifact.** The reusable model → `concepts/patterns/`; the concrete platform-specific instance → `resources/artifacts/`, which references the pattern and lists its implementation files. Never file a pattern under artifacts, or a concrete deliverable under patterns.
20. **Steps declare Input → Output.** Every `people/steps/step-*.md` page states its Input and Output; the process step table carries Input/Output columns; chained step outputs compose into the artifact the process produces.
21. **Categorization tie-breakers.** SDK/service/engine/UI module = **component**; abstract reusable model = **pattern**; concrete produced/consumed file = **artifact**; user-facing capability = **feature** (regardless of lifecycle — legacy/deprecated stays a feature). See Decomposition Rule 7 for the test.
22. **Unresolved entities stay plain text.** Never write a `[[wikilink]]` for a person/product/system you have not resolved against existing pages. Transcripts mangle proper nouns and collapse speakers — confirm garbled names, lone initials, and inferred roles before linking; leave the rest as plain text flagged for review.
23. **Detect duplicate sources.** Before ingesting, check whether the source (or its recording/export) is already ingested. A duplicate becomes a note on the existing source page — do not re-assert its claims into wiki pages.
24. **Integrate, don't duplicate — at the section level.** Rule 9 says prefer updating pages; this extends it to sub-topics: if another page already covers a sub-topic well, link to it rather than writing an overlapping section.
25. **Flag uncertain content as Caveats.** Reconstructed field names, numeric inconsistencies, single-source generalizations, and unverified metrics are marked with a `> **Caveat:**` note — never silently stated as fact.
26. **Settled decisions → ADR synthesis; open decisions → DRAFT.** A decision that has been made (with alternatives weighed) is an ADR-style page in `wiki/synthesis/`; a decision still under investigation is a DRAFT option page (Decomposition Rule 6). Tag content maturity (MVP / v1 / v2 / proposed) so the wiki never overstates commitment.

## Image Handling

1. Store images in `raw/assets/`
2. Reference from wiki: `![description](../raw/assets/image-name.png)`
3. During ingestion, describe important images in text form

## Lint Frequency

- After every 10 ingests
- Monthly at minimum
- Before any major query or synthesis
