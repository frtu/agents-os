---
id: 202608152112-01
title: Product Principles & Core Invariants
spec: 01-principles
layer: core
status: draft
lifecycle: draft
Category: spec
Tags: [principles, invariants, non-goals, governance]
traceability:
  readme: ["§2 Product Principles", "§28 Core Invariants", "§29 Initial Non-Goals"]
  references: ["_references_/0-context/llm-wiki.md", "_references_/10-internal-storage/wiki-schema.md"]
related:
  - "[[00-product-vision]]"
  - "[[03-workspace]]"
  - "[[05-zettelkasten]]"
  - "[[10-risk-engine]]"
Created: 2026-08-15
Last Updated: 2026-08-15
---

# Product Principles & Core Invariants

These principles are binding constraints on every implementation decision. Where a design choice conflicts with a principle, the principle wins.

> **Governance note.** [`memory/constitution.md`](../memory/constitution.md) is the ratified, versioned governance layer derived from these principles (plus continuous spec-gen, risk-governed mutations, and multi-workspace). Every `plan.md` must pass a Constitution Check. When the constitution and a spec disagree, the constitution wins; conflicts with the remote source are recorded in `*-contradiction.md` and indexed in [[clarification]].

## 1. Product Principles

### P1 — Knowledge compounds
The assistant must not behave as a conventional RAG system that reconstructs knowledge from raw documents on every query. It incrementally maintains a persistent wiki: existing concepts are updated, new concepts created, relationships added, contradictions identified, obsolete knowledge challenged, and useful knowledge made increasingly reusable. See [[05-zettelkasten]].

### P2 — Raw information is preserved
Raw inputs are never rewritten as part of knowledge processing. The raw layer is the provenance-preserving source of truth. Immutable raw sources are separated from the generated wiki. See [[03-workspace]].

### P3 — The Vault is an internal product capability
The Vault is owned and maintained by the assistant application. It is **not** Jira, Linear, Azure DevOps, a generic PM database, or a user-facing document-management system. It exists to make the assistant progressively better at reasoning and specification generation.

### P4 — Human remains in control of consequential work
The assistant is autonomous in ingestion, analysis, synthesis, draft generation, and knowledge maintenance — but substantial work stays reviewable. The interaction model is: `Request → Knowledge Retrieval → Plan → User Review → (Critique→Revise | Approve) → Execute → Draft → Feedback → Final`. See [[09-planning]].

## 2. Core Invariants

The implementation MUST preserve these invariants. They are the acceptance backbone for [[20-testing]].

### Knowledge
1. Raw sources are never destructively rewritten.
2. Every processed source retains provenance.
3. Every concept has a stable ID (time-based, in frontmatter).
4. Concepts are normally atomic.
5. Concept relationships use Obsidian `[[wikilinks]]`.
6. Concept usage is tracked separately via `referenced-to`.

### Automation
7. New files under `vault/raw/{any-path}/` automatically trigger ingestion.
8. Conversations are automatically persisted (sessions → dreaming → sources). See [[06-conversations]].
9. Knowledge mutations produce Git commits.
10. Risky mutations use feature branches. See [[10-risk-engine]].
11. `vault/wiki/portal.md` is updated on every ingest.
12. `vault/wiki/log.md` is append-only; existing entries are never edited.

### Specifications
13. Specifications are composed of linked documents.
14. Specification drafts can evolve continuously.
15. Approved specifications are not silently overwritten — changes create a new proposed revision.
16. Git provides the authoritative change history.
17. Specification lifecycle and Git lifecycle remain related but distinct. See [[08-specification-lifecycle]].

### Interaction
18. Significant work starts with a plan.
19. Users can criticize and revise plans.
20. The assistant asks clarification when ambiguity materially matters. See [[09-planning]].
21. Chat and API use the same business capabilities. See [[13-api]], [[14-chat]].
22. External PM actions occur only on user demand. See [[15-integrations]].

## 3. Initial Non-Goals

The first version will NOT:

- replace an external project-management platform;
- become a general-purpose Jira/Linear alternative;
- automatically synchronize every PM artifact;
- make all knowledge changes require human approval;
- make the Vault dependent on a proprietary database;
- replace Markdown/Obsidian as the human-readable representation;
- treat vector embeddings as the canonical knowledge model;
- autonomously execute arbitrary external actions without user intent.

## 4. Precedence Rule

When the README conflicts with the canonical references (`_references_/10-internal-storage/*`), the references take precedence (README §32). This spec kit records such conflicts explicitly where they occur (e.g. spec-kit path: `vault/wiki/product/specs/` per wiki-schema, not `vault/wiki/specs/`).
