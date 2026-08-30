# Spec Kit — Build Specification for the Project Specification Assistant

This directory is a **build spec kit**: a connected set of specification documents an AI (or human) can consume to **build the assistant** described in the project [`REAME.md`](../REAME.md). 

It follows the **GitHub Spec-Kit standard** (ratified constitution → spec → plan → tasks), with the 21 numbered docs as the primary spec.

> **Two spec kits, do not confuse them:**
> - **This kit (`specs/`)** — how to *build* the assistant. Static input to development.
> - **The runtime kit (`vault/wiki/product/specs/`)** — produced and maintained *by* the finished assistant from its Knowledge Vault. Not created here.

## Repository structure (Spec-Kit standard)

```text
templates/                        # externalized, human-owned OUTPUT templates (reuse-before-create)
memory/constitution.md            # ratified, versioned governance (13 principles) — the compliance gate
specs/
├── 00–20 *.md                    # PRIMARY spec (the 21 numbered docs) — authoritative
├── 21-outputs.md                 # extension: secondary PO/PM output capability
├── _templates/                   # adopted spec-kit meta-templates (spec/plan/tasks)
├── 001-leader-assistant/         # buildable layer
│   ├── plan.md                   # decided tech stack + architecture; Constitution Check
│   ├── plan-tbd.md               # open implementation choices (not decided)
│   └── tasks.md                  # ordered build steps tied to the local spec
└── NNN-<feature>/spec.md         # feature specs; each amends the numbered MOCs it touches
```

Feature specs (002 onward) refine the numbered MOCs; where they disagree, the **later feature wins**
and the MOC carries an in-place amendment note. The approval model has been revised three times —
read them in order: [`009-approval-optimization`](009-approval-optimization/spec.md) (effect tiers) →
[`010-agent-approval-channel`](010-agent-approval-channel/spec.md) (the agent's ask channel) →
[`011-maker-checker-approval`](011-maker-checker-approval/spec.md) (**current**: three independent
layers + concierge + learning checker; supersedes 009 FR-3 and 010 FR-2, and drove Constitution
2.0.0).

## Sources of Truth

Derived from the README and the canonical references. When README and references conflict, **references win** (README §32):

- [`REAME.md`](../REAME.md) — vision and narrative.
- [`_references_/0-context/llm-wiki.md`](../_references_/0-context/llm-wiki.md) — the LLM Wiki pattern.
- [`_references_/0-context/Introduction to the Zettelkasten Method • Zettelkasten Method.md`](../_references_/0-context/Introduction%20to%20the%20Zettelkasten%20Method%20%E2%80%A2%20Zettelkasten%20Method.md) — Zettelkasten principles.
- [`_references_/10-internal-storage/wiki-schema.md`](../_references_/10-internal-storage/wiki-schema.md) — canonical directory structure, page format, operations.
- [`_references_/10-internal-storage/wiki-architecture.md`](../_references_/10-internal-storage/wiki-architecture.md) — six categories and articulation.

## Layout

**Core (00-02)** — foundational, change infrequently. **MOCs (03-20, 22)** — evolving Maps of Content that link concerns together. **21** — outputs extension.

| # | Document | Covers | README |
|---|----------|--------|--------|
| 00 | [product-vision](00-product-vision.md) | vision, output, long-term loop | §1, §3, §30 |
| 01 | [principles](01-principles.md) | principles, core invariants, non-goals | §2, §28, §29 |
| 02 | [domain-model](02-domain-model.md) | entities, categories, frontmatter | §10, §28 |
| 03 | [workspace](03-vault.md) | skills/sessions/vault (raw/wiki/output), Git ledger | §6, §10, §27 |
| 04 | [knowledge-ingestion](04-knowledge-ingestion.md) | event-driven ingest pipeline | §8, §12, §13.1, §20 |
| 05 | [zettelkasten](05-zettelkasten.md) | identity, atomicity, status, staleness | §11, §19 |
| 06 | [conversations](06-conversations.md) | sessions, dreaming, promotion | §9, §12 |
| 07 | [specification-model](07-specification-model.md) | spec collection, graph, continuous gen | §3, §4, §13, §21, §25, §31 |
| 08 | [specification-lifecycle](08-specification-lifecycle.md) | draft→review→approved | §5, §24 |
| 09 | [planning](09-planning.md) | plan-first, clarification | §2.4, §14, §15 |
| 10 | [risk-engine](10-risk-engine.md) | extensible risk rules, branching | §7, §22 |
| 11 | [git-workflow](11-git-workflow.md) | commits, branches, review | §6, §23 |
| 12 | [assistant](12-assistant.md) | engines / architecture | §18-§22 |
| 13 | [api](13-api.md) | API surface, parity | §17, §18 |
| 14 | [chat](14-chat.md) | chat interface, parity | §17, §9, §14 |
| 15 | [integrations](15-integrations.md) | external PM, output→knowledge | §16, §26 |
| 16 | [workflows](16-workflows.md) | four operations, orchestration | §12, §13 |
| 17 | [observability](17-observability.md) | portal, log, lint, audit | §27, §12 |
| 18 | [security](18-security.md) | immutability, human control, secrets | §2.2, §2.4, §7, §16, §29 |
| 19 | [non-functional](19-non-functional.md) | portability, scalability, non-goals | §28, §29, §10 |
| 20 | [testing](20-testing.md) | invariant test matrix, acceptance | §28, §13, §12 |
| 21 | [outputs](21-outputs.md) | *extension:* secondary PO/PM outputs, template reuse | §3, §16, §26 |
| 22 | [metadata-management](22-metadata-management.md) | foundation docs (wiki-schema/architecture): bootstrap, core+extension, traceability | §10, §11, §32 |

## Reading Order

0. **Ratified governance first**: [`memory/constitution.md`](../memory/constitution.md) — the 13 principles every plan is checked against.
1. **Understand the product**: 00 → 01 → 02.
2. **Build the knowledge platform**: 03 → 04 → 05 → 06.
3. **Build specification generation**: 07 → 08 → 09.
4. **Add governance**: 10 → 11.
5. **Build interfaces & architecture**: 12 → 13 → 14 → 15.
6. **Cross-cutting**: 16 → 17 → 18 → 19 → 20.
7. **Secondary capability**: 21 (outputs) + root [`templates/`](../templates/).
   **Metadata contract**: 22 (foundation-doc management) — read alongside 03/04 and feature 007.
8. **Build it**: [`001-leader-assistant/plan.md`](001-leader-assistant/plan.md) → [`plan-tbd.md`](001-leader-assistant/plan-tbd.md) → [`tasks.md`](001-leader-assistant/tasks.md), tracking open items in [`clarification.md`](clarification.md).

## Conventions

- Every doc has YAML frontmatter with a stable `id`, `layer` (core|moc), `lifecycle` (draft|review|approved), and a `traceability` block pointing back to README sections and references.
- Cross-references use Obsidian `[[wikilinks]]` (e.g. `[[10-risk-engine]]`).
- Each doc ends with **Acceptance Criteria**; [20-testing](20-testing.md) aggregates the Core Invariants into a test matrix.

## Status

All documents are `lifecycle: draft`. Advance them via [08-specification-lifecycle](08-specification-lifecycle.md) as they are reviewed and approved.
