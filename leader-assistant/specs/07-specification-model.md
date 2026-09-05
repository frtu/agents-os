---
id: 202608152112-07
title: Specification Model
spec: 07-specification-model
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [specification, moc, spec-graph, continuous-generation]
traceability:
  readme: ["§3 Primary Product Output", "§4 Continuous Specification Generation", "§13 Specification Generation Pipeline", "§21 Specification Engine", "§25 Specification Graph", "§31 Spec-Kit Baseline"]
  references: ["_references_/10-internal-storage/wiki-schema.md", "_references_/10-internal-storage/wiki-architecture.md"]
related:
  - "[[00-product-vision]]"
  - "[[05-zettelkasten]]"
  - "[[08-specification-lifecycle]]"
  - "[[09-planning]]"
Created: 2026-08-15
Last Updated: 2026-08-15
---

# Specification Model

Specifications are the assistant's primary output: a **collection of linked documents**, not a monolith. At runtime the assistant maintains them under `vault/wiki/product/specs/`. This spec defines their structure, generation, and graph.

## 1. Two Layers

**Core specification documents (00-02)** — foundational, change infrequently:

```text
vault/wiki/product/specs/
├── 00-product-vision.md   (or 01-product.md)
├── 01-principles.md
└── 02-domain-model.md
```

**Maps of Content (MOCs) — 03+** — Obsidian structure notes that evolve continuously as the wiki grows. They are living navigation documents, not static specs, linking to:
- atomic concepts in `vault/wiki/concepts/`
- product features in `vault/wiki/product/`
- processes/workflows in `vault/wiki/people/`
- components/artifacts in `vault/wiki/resources/`

Example runtime MOC set (README §3): `03-requirements`, `04-user-stories`, `05-workflows`, `06-api`, `07-ui`, `08-non-functional`, `09-acceptance`. The exact set evolves with the project.

## 2. Continuous Generation

Specification generation is continuous — the assistant does **not** require "Generate the specification."

```text
New source → knowledge ingestion → new concept
  → existing project relevance detected
  → specification impact analysis
  → draft specification update
```

Drafts are maintained continuously; changes are made visible through Git and the specification lifecycle ([[08-specification-lifecycle]]).

## 3. Generation Pipeline (README §13)

```text
Knowledge change → impact analysis → identify affected specifications
  → generate/update draft documents → link specifications
  → run consistency checks → risk evaluation → Git commit / feature branch
```

See [[04-knowledge-ingestion]] (upstream), [[10-risk-engine]] and [[11-git-workflow]] (governance).

## 4. Specification Graph

Specs link to one another; a spec should be understandable independently where possible, while references establish system context.

```text
Product Specification
   ├── Domain Model ── API Specification
   ├── User Stories ── Acceptance Criteria
   ├── Workflow Specification
   └── Non-Functional Requirements
```

The Specification Engine maintains these relationships automatically. Concept usage is recorded via `referenced-to` ([[05-zettelkasten]]).

## 5. Specification Engine Responsibilities (README §21)

maintain spec documents · identify gaps · create drafts · update from new knowledge · maintain cross-document links · detect inconsistencies · track lifecycle · connect specs to concepts · support review and approval.

## 6. Frontmatter for Spec Documents

```yaml
---
id: 202608...           # stable
title: ...
layer: core | moc
lifecycle: draft | review | approved
Category: spec
referenced-to: [...]     # concepts/outputs that fed this spec
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
---
```

## 7. Acceptance Criteria

- AC1: The spec set forms a connected document graph (no orphan specs).
- AC2: Core specs (00-02) exist before MOCs are generated.
- AC3: A knowledge change that is project-relevant produces/updates at least one draft spec automatically.
- AC4: Consistency checks run before a spec change is committed.
- AC5: Every spec records the concepts it draws on via `referenced-to`.
