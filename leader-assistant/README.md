# AI Product Owner & Project Specification Assistant

## 1. Vision

This project is an **AI Product Owner / Project Manager assistant** whose primary purpose is to continuously transform accumulated knowledge into **high-quality project specifications**.

The assistant is itself the application being built.

It is accessible through two equivalent interfaces:

- **Application Chat**
- **API**

The assistant maintains an internal **Knowledge Vault** that compounds over time.

The Vault is not the user's external project-management system.

Instead:

```text
                         ┌─────────────────────┐
                         │  Assistant (this    │
                         │      project)       │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
      Knowledge Vault          Specification          External PM
       (internal)                Generation              System
             │                      │                      │
       learns from               produces              invoked on
       raw sources              project specs          user demand
```

The Knowledge Vault is continuously built and maintained by the assistant.

An external project-management system is accessed **only when explicitly requested by the user**, for example:

> "Create a new story for XXX."

---

# Core Concepts: Capture vs Ingest

Two words that are easy to conflate but are deliberately distinct in this system. Keeping
them separate is what lets the raw layer stay immutable (§2.2) while the wiki compounds
(§2.1).

## Capture — an input mechanism, no processing

**Capture** is the sanctioned way human content lands in `vault/raw/`. It is *only* an
input mechanism: it deposits bytes and preserves provenance. It performs **no knowledge
processing** — no summarizing, no classification, no wiki mutation. Nothing derived is
produced.

- Channels: the UI upload panel, the API upload route, or an assistant depositing a
  human-provided source on the human's behalf.
- Destination: `vault/raw/<provenance>/…`, which is **human-owned** (Constitution P2).
- Guarantee: capture never triggers, and is never blocked by, the internal pipeline.
  A captured file simply *exists* in `raw/`, ready to be ingested later.

> Naming: the concept previously described as the "human channel to `vault/raw/`",
> "upload", or "deposit_raw" is unified under **capture**.

## Ingest — the internal workflow, built bottom-up

**Ingest** is the internal **workflow** that consumes *captured* content and organizes it
into durable knowledge (`vault/raw/ → vault/wiki/`). Unlike capture, ingest is where all
the processing happens: read the raw source, produce a source summary, update the wiki
categories, refresh `portal.md`, append `log.md`, commit.

Ingest is built **bottom-up**, in layers, so the actual reasoning lives in a reusable
compute unit (a skill) that the application orchestrates but never rewrites:

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Capability          capabilities.ingest — orchestrates the workflow, │
│                     picks captured sources, invokes the activity,     │
│                     records the report (offline fallback if no SDK)   │
├─────────────────────────────────────────────────────────────────────┤
│ Implementation      activity_ingest.py — the "uber package": injects  │
│  (wrapper)          runtime context (path mapping raw/ ↔              │
│                     {workspace}/vault/raw/) into the skill WITHOUT     │
│                     modifying the skill; two-phase headless bridge     │
├─────────────────────────────────────────────────────────────────────┤
│ Interface           the activity contract: Input Object (parameters)  │
│  (contract)         → Output Object (progress list + error list),     │
│                     as pydantic classes                                │
├─────────────────────────────────────────────────────────────────────┤
│ Activity            the compute unit — provided by the skill           │
│  (compute unit)     `second-brain-ingest`, run headless. Never edited  │
│                     by the app; context is injected around it.         │
└─────────────────────────────────────────────────────────────────────┘
```

**The activity** is the lowest layer: a skill (`second-brain-ingest`) that already knows
how to turn raw sources into wiki knowledge. The app treats it as a black box and never
modifies it.

**The interface** is a contract: an Input Object (the parameters the activity needs) and
an Output Object (a **progress list** and an **error list**), both pydantic classes. Any
activity that fits this contract is interchangeable.

**The implementation** (`activity_ingest.py`) is the "uber package" that fits the
interface and bridges to a **headless** agent run. It injects runtime context — most
importantly the path mapping between the skill's assumed layout (`raw/`, `wiki/`) and this
workspace's real layout (`{workspace}/vault/raw/`, `{workspace}/vault/wiki/`) — as prompt
context, so the skill runs unmodified. It runs in **two phases**:

1. **Run the activity headless.** Build the context, inject the parameters, invoke the
   skill, and collect its (unstructured) output.
2. **Coerce to the contract.** Call headless *again* to reshape that unstructured output
   into the structured pydantic Output Object (progress + errors).

**The capability** (`capabilities.ingest`) sits on top: it selects which captured sources
to process, invokes the activity through the interface, and turns the Output Object into
the workflow's report — with the current in-process logic kept as an offline fallback when
the agent runtime is unavailable.

## Foundation docs: shared truth + per-workspace extension

The activity's skill expects foundation docs (`wiki-schema.md`, `wiki-architecture.md`).
On workspace create, these are **copied** into `vault/docs/` so the activity always has
them locally. Alongside each copy, the workspace also gets an **extension** doc:

- `vault/docs/wiki-schema.md` / `wiki-architecture.md` — the shared foundation, copied
  verbatim and **never modified**.
- `vault/docs/wiki-schema-extension.md` / `wiki-architecture-extension.md` — per-workspace
  overrides that **reference** the common docs and may extend or override them (e.g. map
  the layout paths `raw/ → vault/raw/`, `wiki/ → vault/wiki/`, index `→ portal.md`).

This keeps the shared truth immutable while letting each workspace adapt paths without
forking the foundation.

---

# 2. Product Principles

## 2.1 Knowledge compounds

The assistant should not behave as a conventional RAG system that reconstructs knowledge from raw documents every time.

Instead, it incrementally maintains a persistent wiki.

New sources should be integrated into the existing knowledge base:

- existing concepts are updated
- new concepts are created
- relationships are added
- contradictions are identified
- obsolete knowledge can be challenged
- useful knowledge becomes increasingly reusable

This follows the supplied LLM Wiki model of a persistent, compounding artifact.

---

## 2.2 Raw information is preserved

Raw inputs are never rewritten as part of knowledge processing.

The raw layer is the provenance-preserving source of truth.

The LLM Wiki reference explicitly separates immutable raw sources from the generated wiki.

---

## 2.3 The Vault is an internal product capability

The Vault is owned and maintained by the assistant application.

It is not itself:

- Jira
- Linear
- Azure DevOps
- a generic project-management database
- a user-facing document-management system

The Vault exists to make the assistant progressively better at reasoning and specification generation.

---

## 2.4 Human remains in control of consequential work

The assistant should be autonomous in:

- ingestion
- analysis
- synthesis
- draft generation
- knowledge maintenance

But substantial work should remain reviewable.

The general interaction model is:

```text
User Request
     │
     ▼
Knowledge Retrieval
     │
     ▼
Plan
     │
     ▼
User Review
     │
     ├── Critique ──► Revised Plan
     │
     └── Approve
             │
             ▼
          Execute
             │
             ▼
       Draft Output
             │
             ▼
       User Feedback
             │
             ▼
       Final Output
```

---

# 3. Primary Product Output

The primary output of the assistant is:

> **Project specifications.**

The assistant should continuously generate and refine specifications from:

- accumulated knowledge
- conversations
- source documents
- user requirements
- project context
- previous specifications
- user feedback

The specification is not one monolithic document.

It is a **collection of linked specification documents** stored under `wiki/specs/`.

The specification structure has two layers:

### Core Specification Documents (01-02)

These are foundational specifications that define the product:

```text
wiki/specs/
├── 01-product.md          # Product vision and goals
└── 02-domain.md           # Domain model and entities
```

### Maps of Content (MOCs) — 03+

Documents 03 and beyond are **Maps of Content (MOCs)** — Obsidian structure notes that organize knowledge by domain pillars.

MOCs evolve continuously as the wiki grows. They are not static specifications but living navigation documents that link to:

- atomic concepts in `wiki/concepts/`
- product features in `wiki/product/`
- processes and workflows in `wiki/people/`
- components and artifacts in `wiki/resources/`

Example MOC structure:

```text
wiki/specs/
├── ...
├── 03-requirements.md     # MOC → links to product/features, product/entities, acceptance criteria
├── 04-user-stories.md     # MOC → links to product/persona, product/features
├── 05-workflows.md        # MOC → links to people/processes, people/steps, resources/components
├── 06-api.md              # MOC → links to product/entities, product/features, resources/tools
├── 07-ui.md               # MOC → links to resources/components, product/persona, product/features
├── 08-non-functional.md   # MOC → links to concepts/patterns, product/features, resources/dependencies
└── 09-acceptance.md       # MOC → links to product/features, product/entities, resources/artifacts, tests
```

The knowledge categories referenced in MOCs follow the wiki-architecture:

- **Product** (organized by type: entities, features, personas)
- **People** (processes, steps, roles, competencies, members)
- **Concepts** (patterns, technologies)
- **Resources** (artifacts, components, dependencies, tools)

The important invariant is that specifications form a connected document graph with the wiki knowledge base.

---

# 4. Continuous Specification Generation

Specification generation is continuous.

The assistant does not require the user to explicitly say:

> "Generate the specification."

Instead, relevant knowledge changes can cause specification drafts to be created or updated.

For example:

```text
New source
   │
   ▼
Knowledge ingestion
   │
   ▼
New concept
   │
   ▼
Existing project relevance detected
   │
   ▼
Specification impact analysis
   │
   ▼
Draft specification update
```

The assistant should maintain draft specifications continuously while making the changes visible through Git and the specification lifecycle.

---

# 5. Specification Lifecycle

Specifications have a semantic lifecycle:

```text
                 ┌─────────┐
                 │  draft  │
                 └────┬────┘
                      │
                   review
                      │
                      ▼
                 ┌─────────┐
                 │ review  │
                 └────┬────┘
                      │
                   approve
                      │
                      ▼
                ┌──────────┐
                │ approved │
                └────┬─────┘
                     │
              proposed change
                     │
                     ▼
                  draft
```

Additional lifecycle states may be introduced later, such as:

- `superseded`
- `deprecated`
- `rejected`

The lifecycle is semantic.

Git remains the technical mechanism providing:

- history
- diffs
- branches
- commits
- rollback
- review
- merge

Therefore:

```text
Specification lifecycle
        +
Git lifecycle
```

are related but not identical.

---

# 6. Git as the Knowledge and Specification Ledger

The Vault is a Git repository of Markdown documents.

Every meaningful mutation is captured as a Git commit.

This includes:

- raw ingestion metadata
- source creation
- source updates
- concept creation
- concept modification
- concept deletion
- specification changes
- conversation capture
- generated artifacts

The supplied LLM Wiki reference explicitly identifies the wiki as a Git repository of Markdown files, providing version history and branching.

---

# 7. Risk-Based Branching

Not every change should be made directly to the main branch.

The assistant evaluates changes using an **extensible risk-rule engine**.

Conceptually:

```text
Change
  │
  ▼
Risk Evaluation
  │
  ├── safe ───────► commit to main
  │
  └── risky ──────► feature/{feature-name}
                           │
                           ▼
                       commits
                           │
                           ▼
                      user review
                           │
                           ▼
                         merge
```

The risk system must be extensible.

Risk rules are configuration/domain objects rather than hard-coded `if` statements spread throughout the application.

An initial rule may identify:

> A proposed change contradicts existing knowledge.

Future rules may identify:

- modification of a reliable concept
- deletion of a highly referenced concept
- large-scale concept changes
- modification of many interconnected concepts
- modification of approved specifications
- potentially destructive changes
- changes with insufficient provenance
- changes affecting many Areas
- conflicting sources
- semantic uncertainty

The exact rules will be specified later.

---

# 8. Automatic Ingestion

The ingestion pipeline is event-driven.

Whenever a new document is stored anywhere under:

```text
raw/
```

the assistant automatically starts ingestion.

This includes arbitrary subdirectories.

For example:

```text
raw/
├── articles/
│   └── article.md
├── zoom/
│   └── meeting-2026-08-12.md
├── voice/
│   └── idea.md
└── imported/
    └── notes.md
```

All of these are ingestion candidates.

The fundamental invariant is:

```text
raw/{any-path}/{document}
              │
              ▼
       ingestion trigger
```

The user should not need to manually tell the assistant:

> "Process this file."

---

# 9. Conversation Capture

Every application conversation is captured automatically.

Conversation threads are stored under `sessions/` for empheral capture (short term memory):

```text
sessions/
├── conversation-2026-08-12-project-spec.md
├── conversation-2026-08-12-codename-discussion.md
└── ...
```

A conversation is therefore both:

1. an interaction mechanism that is more volatile (operational)
2. knowledge patch candidate to be filtered & complement part of the durable knowledge source (in `wiki/`)

The conversation capture itself is about immediate demand for adhoc operational case resolution, not be confused with the processed knowledge. It may contains judgement (upvote or downvote that should be referenced in the knowledge) or complement on the knowledge.

**Two-stage knowledge promotion pipeline:**

```text
raw/{provenance}/              (immutable source)
     │
     ▼
Conversation
     │
     ▼
sessions/                      (operational capture)
     │
     ▼ DREAMING (daily)
     │
wiki/sources/_daily_/          (daily digest with references to sessions)
     │
     ▼ INGEST
     │
wiki/sources/{provenance}/{source}.md   (source summary — references daily digest, preserves provenance)
     │
     ▼
wiki/{categories}              (standalone knowledge — no session refs)
```

**Key rule**: Final wiki pages contain standalone knowledge. Session references exist only in daily digests; source summaries preserve provenance by mirroring raw/ subfolders; wiki category pages reference source summaries. This keeps the durable knowledge clean while preserving full provenance chain.

---

# 10. Knowledge Layers

The Vault follows the LLM Wiki architecture. For complete directory structure, subdirectories, and their purposes, see:

- **[wiki-schema.md § Architecture](_references_/10-internal-storage/wiki-schema.md#architecture)** — four directories (`raw/`, `wiki/`, `sessions/`, `output/`), all subdirectories, and special files
- **[wiki-architecture.md](_references_/10-internal-storage/wiki-architecture.md)** — six wiki categories and their articulations

High-level overview:

```text
Vault/
├── sessions/     # Operational conversations (short-term) → wiki-schema.md § Sessions
├── raw/          # Immutable sources (never modified) → wiki-schema.md § Raw subdirectories
├── wiki/         # LLM workspace (all knowledge) → wiki-schema.md § Wiki subdirectories
└── output/       # Generated artifacts
```

The wiki organizes knowledge into six categories: **Concepts**, **Product**, **People**, **Resources**, **Projects**, **Synthesis**. See [wiki-architecture.md § Overview](_references_/10-internal-storage/wiki-architecture.md#overview) for full details.

---

# 11. Zettelkasten Model

The `wiki/` layer follows Zettelkasten principles. For complete rules, see **[wiki-schema.md § Zettelkasten Management](_references_/10-internal-storage/wiki-schema.md#zettelkasten-management)**.

Key principles applied:

| Principle | Reference |
|-----------|-----------|
| **Identity** — stable time-based IDs | wiki-schema.md § Identity |
| **Atomicity** — one concept per page | wiki-schema.md § Atomicity |
| **Connections** — explain *why* links exist | wiki-schema.md § Connections |
| **Status lifecycle** — `draft → used → reliable` | wiki-schema.md § Status Lifecycle |
| **referenced-to** — track usage in outputs | wiki-schema.md § referenced-to |
| **Structure Notes (MOCs)** — navigation hubs | wiki-schema.md § Structure Notes |

The assistant should follow these principles when creating and maintaining wiki pages.

---

# 12. Knowledge Operations

The assistant performs four main operations on the wiki. For complete procedures, see **[wiki-schema.md § Operations](_references_/10-internal-storage/wiki-schema.md#operations)**:

| Operation | Purpose | Trigger |
|-----------|---------|---------|
| **Dreaming** | Compact daily sessions into `wiki/sources/_daily_/` digests | End of day / on demand |
| **Ingest** | Process raw sources into wiki knowledge | New file in `raw/` |
| **Query** | Answer questions from wiki with citations | User question |
| **Lint** | Health-check wiki for contradictions, orphans, staleness | Periodic / on demand |

**Knowledge transfer rule**: Final wiki pages contain standalone knowledge. Session references exist only in daily digests. Source summaries preserve provenance by mirroring raw/ structure. The provenance chain is:

```text
raw/{provenance}/ → sessions/ → wiki/sources/_daily_/ → wiki/sources/{provenance}/{source}.md → wiki/{category}/
```

The ingestion pipeline is automatic once material enters `raw/`.

---

# 13. Specification Generation Pipeline

Specification generation follows:

```text
Knowledge change
       │
       ▼
Impact analysis
       │
       ▼
Identify affected specifications
       │
       ▼
Generate/update draft documents
       │
       ▼
Link specifications
       │
       ▼
Run consistency checks
       │
       ▼
Risk evaluation
       │
       ▼
Git commit / feature branch
```

This means specifications can evolve continuously as the knowledge base evolves.

## 13.1. Knowledge Ingestion Pipeline

The initial pipeline is:

```text
-New raw document
-       │
-       ▼
-Detect / classify
-       │
-       ▼
-Read source
-       │
-       ▼
-Normalize
-       │
-       ▼
-Create/update source document
-       │
-       ▼
-Compare with existing wiki
-       │
-       ├── Existing knowledge
-       │
-       ├── New knowledge
-       │
-       ├── Contradiction
-       │
-       └── Uncertainty
-       │
-       ▼
-Generate proposed wiki mutations
-       │
-       ▼
-Risk evaluation
-       │
-       ├── Safe
-       │     └── commit
-       │
-       └── Risky
-             └── feature branch
 ```

---

# 14. Planning-First User Interaction

For an explicit work request, the assistant should first produce a complete plan.

Example:

> "Create a project specification for workflow orchestration."

The assistant should:

1. understand the request
2. inspect relevant Vault knowledge
3. identify missing information
4. ask clarification questions if needed
5. produce a complete plan
6. present the plan
7. allow the user to criticize it
8. revise the plan
9. execute it
10. produce draft specification documents
11. present meaningful alternatives where necessary
12. incorporate feedback

The assistant should not jump directly from request to large-scale execution.

---

# 15. Clarification Behavior

The assistant should ask clarification questions when ambiguity materially affects:

- project scope
- specification structure
- business requirements
- architecture
- external actions
- destructive changes
- knowledge classification
- risk evaluation
- output expectations

It should not ask unnecessary questions when reasonable assumptions can be safely made.

When assumptions are made, they should be explicit.

---

# 16. External Project Management Systems

The external PM system is an integration boundary.

The assistant does not continuously synchronize its entire Vault with a PM system.

Instead, the user explicitly requests actions.

Examples:

```text
"Create a new story for payment reconciliation."

"Update the acceptance criteria of story ABC-123."

"Create these tasks in Jira."

"Move this ticket to In Progress."
```

The assistant should:

1. understand the request
2. use its knowledge and specifications
3. generate a proposed action/plan
4. ask for clarification if needed
5. invoke the external integration
6. capture the resulting output/action
7. optionally feed useful resulting knowledge back into the Vault

---

# 17. API and Chat Parity

Chat and API must expose the same underlying capabilities.

```text
              ┌───────────────┐
              │     Chat      │
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │ Assistant API │
              └───────┬───────┘
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
   Knowledge       Planning      Execution
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                 Specifications
```

The business logic must live below the interface layer.

Chat should not implement capabilities that cannot be invoked through API.

API should not bypass the planning/risk/knowledge model.

---

# 18. Assistant Architecture

The application should conceptually contain:

```text
Assistant
├── Conversation Manager
├── Knowledge Engine
├── Ingestion Engine
├── Zettelkasten Manager
├── Specification Engine
├── Planning Engine
├── Risk Engine
├── Workflow/Execution Engine
├── Git/Vault Manager
└── Integration Manager
```

These are logical components, not necessarily separate deployable services.

---

# 19. Knowledge Engine

Responsibilities:

- search Vault
- identify relevant concepts
- resolve Obsidian links
- inspect Areas
- identify source provenance
- detect concept relationships
- identify contradictions
- track concept usage
- evaluate concept maturity
- maintain indexes

---

# 20. Ingestion Engine

Responsibilities:

- detect raw documents
- classify source type
- normalize source
- generate source documents
- extract knowledge candidates
- compare against existing knowledge
- generate wiki changes
- invoke risk evaluation
- commit or branch

---

# 21. Specification Engine

Responsibilities:

- maintain specification documents
- identify specification gaps
- create draft specifications
- update specifications from new knowledge
- maintain cross-document links
- detect specification inconsistencies
- track lifecycle
- connect specifications to concepts
- support review and approval

---

# 22. Risk Engine

Risk evaluation must be rule-driven.

Conceptually:

```text
RiskRule
├── id
├── description
├── scope
├── condition
├── severity
└── action
```

The rule set must be extensible without redesigning the ingestion engine.

Initial rules may include:

```text
CONTRADICTION_WITH_EXISTING_KNOWLEDGE
CHANGE_RELIABLE_CONCEPT
LARGE_KNOWLEDGE_MUTATION
DELETE_REFERENCED_CONCEPT
MODIFY_APPROVED_SPEC
LOW_PROVENANCE_CONFIDENCE
```

These are examples, not yet the final rule set.

---

# 23. Git Workflow

Normal change:

```text
change
  ↓
risk evaluation
  ↓
safe
  ↓
commit main
```

Risky change:

```text
change
  ↓
risk evaluation
  ↓
risky
  ↓
feature/{feature-name}
  ↓
commit(s)
  ↓
review
  ↓
merge
```

The assistant should never silently merge a risky branch without the appropriate approval policy being satisfied.

---

# 24. Specification Review

A specification can be:

```text
draft
```

for continuous assistant generation.

When the user reviews it:

```text
draft → review
```

After approval:

```text
review → approved
```

Future assistant changes to an approved specification should create a new proposed revision rather than silently replacing the approved state.

Conceptually:

```text
Approved Specification
        │
        │ new knowledge
        ▼
Proposed Revision
        │
        ▼
Draft
        │
        ▼
Review
        │
        ▼
Approved
```

Git history provides the underlying exact changes.

---

# 25. Specification Graph

Specifications should link to one another.

Example:

```text
Product Specification
       │
       ├── Domain Model
       │      │
       │      └── API Specification
       │
       ├── User Stories
       │      │
       │      └── Acceptance Criteria
       │
       ├── Workflow Specification
       │
       └── Non-Functional Requirements
```

The assistant should maintain these relationships automatically.

A specification should be understandable independently where possible, while references establish the larger system context.

---

# 26. Output → Knowledge Feedback

Specifications and other generated artifacts can become inputs to the knowledge system.

After generating an output, the assistant should evaluate:

- which concepts were used
- whether existing concepts required correction
- whether new concepts emerged
- whether a contradiction was discovered
- whether the specification exposed missing knowledge
- whether concept usage should be recorded

This creates:

```text
Knowledge
   ↓
Specification
   ↓
Review
   ↓
Feedback
   ↓
Improved Knowledge
```

The Zettelkasten source similarly describes project work as producing valuable byproducts that can become future knowledge.

---

# 27. Portal and Log

The wiki maintains two special files. For format details, see **[wiki-schema.md § Index Format](_references_/10-internal-storage/wiki-schema.md#index-format)** and **[wiki-schema.md § Log Format](_references_/10-internal-storage/wiki-schema.md#log-format)**.

- **`wiki/portal.md`** — master catalog of every wiki page, updated on every ingest
- **`wiki/log.md`** — chronological append-only operational record

---

# 28. Core Invariants

The implementation must preserve these invariants.

### Knowledge

1. Raw sources are never destructively rewritten.
2. Every processed source retains provenance.
3. Every concept has a stable ID.
4. Concepts are normally atomic.
5. Concept relationships use Obsidian links.
6. Concept usage is tracked separately through `referenced-to`.

### Automation

7. New files under `raw/` automatically trigger ingestion.
8. Conversations are automatically persisted to `raw/notes/`.
9. Knowledge mutations produce Git commits.
10. Risky mutations use feature branches.
11. Portal (`wiki/portal.md`) is updated on every ingest.
12. Log (`wiki/log.md`) is append-only.

### Specifications

11. Specifications are composed of linked documents.
12. Specification drafts can evolve continuously.
13. Approved specifications are not silently overwritten.
14. Git provides the authoritative change history.
15. Specification lifecycle and Git lifecycle remain distinct.

### Interaction

16. Significant work starts with a plan.
17. Users can criticize and revise plans.
18. The assistant asks clarification when ambiguity materially matters.
19. Chat and API use the same business capabilities.
20. External PM actions occur only on user demand.

---

# 29. Initial Non-Goals

The first version will not attempt to:

- replace an external project-management platform
- become a general-purpose Jira/Linear alternative
- automatically synchronize every PM artifact
- make all knowledge changes require human approval
- make the Vault dependent on a proprietary database
- replace Markdown/Obsidian as the human-readable representation
- treat vector embeddings as the canonical knowledge model
- autonomously execute arbitrary external actions without user intent

---

# 30. Long-Term Product Loop

The intended long-term behavior is:

```text
                    ┌─────────────────┐
                    │  Raw Knowledge  │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │    Ingestion    │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Knowledge Vault │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Specification   │
                    │    Drafting     │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Human Review    │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │   Approved      │
                    │ Specification   │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ External PM     │
                    │ Actions on      │
                    │ User Request    │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Feedback / New  │
                    │    Knowledge    │
                    └────────┬────────┘
                             │
                             └──────────► Knowledge Vault
```

The ultimate objective is a **knowledge-compounding specification assistant**:

> The more the assistant learns, the better its specifications become; the more specifications are reviewed and used, the more useful knowledge becomes available for future work.

---

# 31. Spec-Kit Baseline

The next specification phase should define the system progressively.

Specifications live under `wiki/specs/` following the LLM Wiki architecture.

The initial Spec-Kit structure:

```text
wiki/specs/
│
├── 00-product-vision.md       # Core specification
├── 01-principles.md           # Core specification
├── 02-domain-model.md         # Core specification
│
│   # MOCs — evolving Maps of Content linking to wiki categories
│
├── 03-vault.md                # MOC → wiki structure, concepts/technologies
├── 04-knowledge-ingestion.md  # MOC → concepts/technologies, people/processes
├── 05-zettelkasten.md         # MOC → concepts/patterns, wiki structure
├── 06-conversations.md        # MOC → people/processes, resources/tools
├── 07-specification-model.md  # MOC → concepts/patterns, product/features
├── 08-specification-lifecycle.md # MOC → product/features, people/processes
├── 09-planning.md             # MOC → people/processes, people/steps
├── 10-risk-engine.md          # MOC → concepts/patterns, product/features
├── 11-git-workflow.md         # MOC → people/processes, resources/tools
├── 12-assistant.md            # MOC → resources/components, product/features
├── 13-api.md                  # MOC → product/features, resources/components
├── 14-chat.md                 # MOC → product/persona, product/features
├── 15-integrations.md         # MOC → resources/dependencies, resources/tools
├── 16-workflows.md            # MOC → people/processes, people/steps
├── 17-observability.md        # MOC → resources/components, product/features
├── 18-security.md             # MOC → concepts/patterns, product/features
├── 19-non-functional.md       # MOC → concepts/patterns, product/entities
└── 20-testing.md              # MOC → people/processes, resources/artifacts
```

This ordering deliberately defines the **domain and knowledge model (00-02) before the evolving MOCs (03+)**.

Core specifications (00-03) are foundational documents that change infrequently.

MOCs (04+) continuously evolve as the wiki grows, linking to atomic concepts, processes, features, and components across wiki categories.

---

# 32. Reference Documents

This README is derived from canonical reference documents in `_references_/`:

| Document | Purpose |
|----------|---------|
| `_references_/0-context/llm-wiki.md` | LLM Wiki pattern — the core architecture of raw → wiki → output |
| `_references_/0-context/Introduction to the Zettelkasten Method.md` | Zettelkasten principles — atomicity, connections, structure notes |
| `_references_/10-internal-storage/wiki-schema.md` | Wiki schema — canonical directory structure, page format, operations |
| `_references_/10-internal-storage/wiki-architecture.md` | Wiki architecture — six categories, domain articulation, AI categorization guide |

These references are the source of truth for:

- Directory structure (`raw/`, `wiki/`, `output/`)
- Wiki subdirectories and their purposes
- Page format and frontmatter schema
- Operations (ingest, query, lint)
- Domain categorization rules

When this README conflicts with the reference documents, the references take precedence.

---

# 33. Implemented API Reference & Testing

Sections 1–32 describe the product. This section documents the **implemented** surface
as it ships today. It is the concrete counterpart to §17 (API and Chat Parity): every
route below is a thin call over the shared capability layer, so chat and REST expose the
same capabilities. See `getting-started.md` for a runnable tour.

## 33.1 Running the service

```bash
uv sync                    # install deps
uv run leader-assistant    # start on http://localhost:8000 (banner prints URLs)
LEADER_PORT=8080 uv run leader-assistant   # change the port
```

Configuration via environment variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `LEADER_VAULT_ROOT` | folder holding `Vaults/<name>/` | `./Vaults` |
| `LEADER_VAULT_PATH` | explicit single-vault path (wins over root) | — |
| `LEADER_DEFAULT_VAULT` | vault used when none is named | `default` |
| `LEADER_HOST` / `LEADER_PORT` | server bind address / port | `127.0.0.1` / `8000` |

## 33.2 Endpoints

Base URL `http://localhost:8000`. Consequential requests return a **plan** for approval
rather than mutating silently (§2.4, spec 13-api AC2).

| Method | Path | Body / params | Returns |
|--------|------|---------------|---------|
| `GET`  | `/` | — | Gradio web UI (spec 003) |
| `GET`  | `/api` | — | Swagger UI |
| `GET`  | `/health` | — | `{"status":"ok"}` |
| `GET`  | `/api/vaults` | — | vaults + resolved root and default |
| `POST` | `/api/vaults` | `{"name":"demo"}` | vault info (`scaffolded`) |
| `GET`  | `/api/vaults/{selector}` | path selector | vault info (path, page count) |
| `POST` | `/api/ingest` | `{vault?, title, content, provenance}` | ingest report (source page, portal updated) |
| `POST` | `/api/query` | `{vault?, question}` | answer + citations |
| `POST` | `/api/plan` | `{vault?, request}` | plan (risk, steps, requires_approval) |
| `GET`  | `/api/lint` | `?vault=<name>` | hygiene findings |
| `GET`  | `/api/spec` | `?path=<rel>&vault=<name>` | `{path, content}` (raw Markdown) |
| `POST` | `/api/chat` | `ChatRequest` | `ChatAnswer` (full reply) |
| `POST` | `/api/chat/stream` | `ChatRequest` | Server-Sent Events of `ChatDelta` |

The human web UI (Gradio, spec 003) owns `/`, so Swagger is relocated to `/api`.
Interactive docs: **Swagger UI** `/api` · **ReDoc** `/redoc` · **OpenAPI JSON**
`/openapi.json`. Full request/response schemas render at `/api`.

## 33.3 Chat request/response shapes

`ChatRequest` (both chat routes):

```json
{
  "message": "your message",
  "vault": "demo",              // optional; omitted = default vault
  "conversation_id": "abc123",  // optional; omitted = start a new thread
  "approve": false              // set true to approve the thread's pending plan
}
```

`ChatAnswer` (`/api/chat`):

```json
{
  "vault": "demo",
  "conversation_id": "<id>",
  "reply": "...",
  "citations": [{"page": "wiki/...", "excerpt": "..."}],
  "pending_plan": null,          // a Plan object when the request is consequential
  "executed": false              // true only on an approved turn that ran the plan
}
```

`ChatDelta` (`/api/chat/stream`): one `data: {json}` line per event carrying the
accumulated `reply`; the final event has `"done": true`. Same fields as `ChatAnswer`
plus `done`. Resend the returned `conversation_id` to continue a thread; conversations
persist one file per thread under `<vault>/sessions/<conversation_id>.md` and resume by
id even after a restart. A consequential request returns a `pending_plan` and mutates
nothing; a follow-up turn with `approve: true` executes it.

> The chat answer path uses the `claude-agent-sdk` runtime (needs the `claude` CLI /
> credentials). When unavailable it falls back to a deterministic cited answer via
> `query`, so the endpoint still works offline. All non-chat routes run with no
> credentials.

## 33.4 Testing

The suite in `tests/` drives the FastAPI app over HTTP; each test maps to a user story /
acceptance criterion — `test_rest_api.py` (§ REST capabilities) and `test_chat_api.py`
(chat AC-1..AC-10). It runs offline and deterministic (chat is forced down its no-LLM
fallback) against a throwaway vault under a temp dir, so it never touches real vaults or
the repo.

```bash
uv run --extra dev pytest                       # full suite (offline)
uv run --extra dev pytest -v                    # one line per test
LEADER_LIVE_AGENT=1 uv run --extra dev pytest   # also run the opt-in live-agent test
```
