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
  - "[[03-workspace]]"
  - "[[05-zettelkasten]]"
  - "[[07-specification-model]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# Domain Model

The core entities the assistant reasons about. Filenames use kebab-case; titles use Title Case; every persisted entity carries YAML frontmatter with a stable time-based `id`.

## 1. Storage-Layer Entities

All storage paths below are relative to a selected workspace `Workspaces/<name>/` (multiple workspaces supported — see [[03-workspace]]). Durable knowledge lives under the workspace's `vault/` subfolder; `sessions/` sits at the workspace level.

| Entity | Location | Mutability | Description |
|--------|----------|------------|-------------|
| **Raw Document** | `vault/raw/{provenance}/{file}` | immutable | Original captured input (clipping, doc, note, transcript, asset). Never modified. |
| **Session** | `sessions/YYYY-MM-DD-HH-MM-SS-<conversation-id>-<slug>.md` | ephemeral | Operational conversation log (short-term memory), at the workspace level. Not part of the wiki. Created **lazily**, on the first user message; the prefix is the `Created` timestamp to the second ([[012-conversation-naming]] FR-1/FR-2/FR-12). |
| **Daily Digest** | `vault/wiki/sources/_daily_/YYYY-MM-DD.md` | append-per-day | Compacted session insights produced by dreaming. |
| **Source Summary** | `vault/wiki/sources/{provenance}/{source}.md` | maintained | One factual summary page per ingested source, mirroring `vault/raw/` for provenance. |
| **Wiki Page** | `vault/wiki/{category}/...` | maintained | Standalone durable knowledge (concept/product/people/resource/project/synthesis). |
| **Specification** | `vault/wiki/product/specs/NN-*.md` | maintained | Linked spec document; core (00-02) or MOC (03+). |
| **Portal** | `vault/wiki/portal.md` | maintained | Master catalog of every wiki page. Updated on every ingest. |
| **Log** | `vault/wiki/log.md` | append-only | Chronological operational record. |
| **Output Artifact** | `vault/output/...` | generated | Reports, query results, generated deliverables. |
| **Installed Skill** | `skills/...` | installed | A skill available to the workspace; a file/folder or a reference-link to another folder. |

## 2. Knowledge Categories (Wiki)

The wiki organizes durable knowledge into six categories (see [[03-workspace]] and wiki-architecture):

1. **Concepts** — `patterns/`, `technologies/` (reusable knowledge).
2. **Product** — `entities/`, `features/`, `persona/` (what we build; flat organization).
3. **People** — `processes/`, `steps/`, `roles/`, `competencies/`, `members/`.
4. **Resources** — `artifacts/`, `components/`, `dependencies/`, `tools/`.
5. **Projects** — `{initiative}/`, `{product}/{project}/` (time-bounded work).
6. **Synthesis** — cross-cutting comparisons and analyses.

## 3. Governance-Layer Entities

| Entity | Fields | Description |
|--------|--------|-------------|
| **Concept Status** | `draft → used → reliable` | Evidence-based maturity; driven by `usage-count`/`referenced-to`, demoted by a big correction. See [[05-zettelkasten]]. |
| **Specification Lifecycle** | `draft → review → approved` (+ future: superseded/deprecated/rejected) | Semantic state of a spec. See [[08-specification-lifecycle]]. |
| **RiskRule** | `id, description, scope, condition, severity, action` | Extensible rule evaluated on every proposed mutation. See [[10-risk-engine]]. |
| **Commit / Branch** | Git objects | Technical ledger backing every mutation. See [[11-git-workflow]]. |
| **Plan** | request, retrieved knowledge, gaps, steps, alternatives | Produced before consequential execution. See [[09-planning]]. |
| **Template** | `output-type`, structure | Externalized, human-owned output structure at repo-root `templates/`; reuse-before-create. See [[21-outputs]]. |
| **Output Artifact** | `vault/output/...`, cites concepts | Produced PO/PM artifact (secondary capability); records usage back to concepts. See [[21-outputs]]. |
| **Workspace** | `Workspaces/<name>/`, selector/default | The top-level container (`skills/`, `sessions/`, `vault/`); its knowledge store is the `vault/` subfolder. Multiple are supported. See [[03-workspace]]. |

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
usage-count: 0            # counter — artifacts that have cited this concept
referenced-to:            # reference — outputs/specs this concept contributed to
  - "[[spec-...]]"
last-correction:          # YYYY-MM-DD; empty until first big correction
---
```

See [[05-zettelkasten]] §4–5 for the lifecycle math over `usage-count` / `referenced-to` / `last-correction`.

## 5. Key Relationships

- **Provenance chain** (invariant): `vault/raw/{provenance}/ → sessions/ → vault/wiki/sources/_daily_/ → vault/wiki/sources/{provenance}/{source}.md → vault/wiki/{category}/`.
- **Standalone-knowledge rule**: final wiki category pages reference source summaries, never sessions or daily digests directly.
- **Category articulation**: concepts→dependencies→tools abstraction ladder; process→steps→artifacts; features→components→artifacts (see wiki-architecture for full articulation).
- **Specification graph**: specs link to each other and to wiki concepts via `referenced-to`. See [[07-specification-model]].

## 6. Naming & Linking Rules

- Filenames: kebab-case `.md`; titles: Title Case.
- Single-word links: `[[Kafka]]`; multi-word: `[[file-link|Display Text]]`; inside tables escape the pipe: `[[domain-developer\|Domain Developer]]`.
- IDs are stable across renames; the filename may change, the `id` must not.
