---
id: 202608132112-02
title: Domain Model
spec: 02-domain-model
layer: core
status: draft
lifecycle: draft
Category: spec
Tags: [domain-model, entities, ontology]
traceability:
  readme: ["§10 Knowledge Layers", "§28 Core Invariants"]
  references: ["_references_/10-internal-storage/wiki-architecture.md", "_references_/10-internal-storage/wiki-schema.md"]
related:
  - "[[00-product-vision]]"
  - "[[03-vault]]"
  - "[[05-zettelkasten]]"
  - "[[07-specification-model]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# Domain Model

The core entities the assistant reasons about. Filenames use kebab-case; titles use Title Case; every persisted entity carries YAML frontmatter with a stable time-based `id`.

## 1. Storage-Layer Entities

| Entity | Location | Mutability | Description |
|--------|----------|------------|-------------|
| **Raw Document** | `raw/{provenance}/{file}` | immutable | Original captured input (clipping, doc, note, transcript, asset). Never modified. |
| **Session** | `sessions/YYYY-MM-DD-*.md` | ephemeral | Operational conversation log (short-term memory). Not part of the wiki. |
| **Daily Digest** | `wiki/sources/_daily_/YYYY-MM-DD.md` | append-per-day | Compacted session insights produced by dreaming. |
| **Source Summary** | `wiki/sources/{provenance}/{source}.md` | maintained | One factual summary page per ingested source, mirroring `raw/` for provenance. |
| **Wiki Page** | `wiki/{category}/...` | maintained | Standalone durable knowledge (concept/product/people/resource/project/synthesis). |
| **Specification** | `wiki/product/specs/NN-*.md` | maintained | Linked spec document; core (00-02) or MOC (03+). |
| **Portal** | `wiki/portal.md` | maintained | Master catalog of every wiki page. Updated on every ingest. |
| **Log** | `wiki/log.md` | append-only | Chronological operational record. |
| **Output Artifact** | `output/...` | generated | Reports, query results, generated deliverables. |

## 2. Knowledge Categories (Wiki)

The wiki organizes durable knowledge into six categories (see [[03-vault]] and wiki-architecture):

1. **Concepts** — `patterns/`, `technologies/` (reusable knowledge).
2. **Product** — `entities/`, `features/`, `persona/` (what we build; flat organization).
3. **People** — `processes/`, `steps/`, `roles/`, `competencies/`, `members/`.
4. **Resources** — `artifacts/`, `components/`, `dependencies/`, `tools/`.
5. **Projects** — `{initiative}/`, `{product}/{project}/` (time-bounded work).
6. **Synthesis** — cross-cutting comparisons and analyses.

## 3. Governance-Layer Entities

| Entity | Fields | Description |
|--------|--------|-------------|
| **Concept Status** | `draft → used → reliable` | Evidence-based maturity; driven by `referenced-to` count. See [[05-zettelkasten]]. |
| **Specification Lifecycle** | `draft → review → approved` (+ future: superseded/deprecated/rejected) | Semantic state of a spec. See [[08-specification-lifecycle]]. |
| **RiskRule** | `id, description, scope, condition, severity, action` | Extensible rule evaluated on every proposed mutation. See [[10-risk-engine]]. |
| **Commit / Branch** | Git objects | Technical ledger backing every mutation. See [[11-git-workflow]]. |
| **Plan** | request, retrieved knowledge, gaps, steps, alternatives | Produced before consequential execution. See [[09-planning]]. |

## 4. Frontmatter Schema (every wiki page)

```yaml
---
Category: wiki
Tags: [tag1, tag2]
Source links:
  - [[source-filename-1.md]]
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
id: 202608120746          # stable time-based ID (YYYYMMDDHHMM)
status: draft             # concept maturity (concept pages)
referenced-to:            # outputs this concept contributed to
  - "[[spec-...]]"
---
```

## 5. Key Relationships

- **Provenance chain** (invariant): `raw/{provenance}/ → sessions/ → wiki/sources/_daily_/ → wiki/sources/{provenance}/{source}.md → wiki/{category}/`.
- **Standalone-knowledge rule**: final wiki category pages reference source summaries, never sessions or daily digests directly.
- **Category articulation**: concepts→dependencies→tools abstraction ladder; process→steps→artifacts; features→components→artifacts (see wiki-architecture for full articulation).
- **Specification graph**: specs link to each other and to wiki concepts via `referenced-to`. See [[07-specification-model]].

## 6. Naming & Linking Rules

- Filenames: kebab-case `.md`; titles: Title Case.
- Single-word links: `[[Kafka]]`; multi-word: `[[file-link|Display Text]]`; inside tables escape the pipe: `[[domain-developer\|Domain Developer]]`.
- IDs are stable across renames; the filename may change, the `id` must not.
