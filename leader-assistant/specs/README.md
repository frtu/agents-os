# Spec Kit — Build Specification for the Project Specification Assistant

This directory is a **build spec kit**: a connected set of specification documents an AI (or human) can consume to **build the assistant** described in the project [`REAME.md`](../REAME.md).

> **Two spec kits, do not confuse them:**
> - **This kit (`specs/`)** — how to *build* the assistant. Static input to development.
> - **The runtime kit (`wiki/product/specs/`)** — produced and maintained *by* the finished assistant from its Knowledge Vault. Not created here.

## Sources of Truth

Derived from the README and the canonical references. When README and references conflict, **references win** (README §32):

- [`REAME.md`](../REAME.md) — vision and narrative.
- [`_references_/0-context/llm-wiki.md`](../_references_/0-context/llm-wiki.md) — the LLM Wiki pattern.
- [`_references_/0-context/Introduction to the Zettelkasten Method • Zettelkasten Method.md`](../_references_/0-context/Introduction%20to%20the%20Zettelkasten%20Method%20%E2%80%A2%20Zettelkasten%20Method.md) — Zettelkasten principles.
- [`_references_/10-internal-storage/wiki-schema.md`](../_references_/10-internal-storage/wiki-schema.md) — canonical directory structure, page format, operations.
- [`_references_/10-internal-storage/wiki-architecture.md`](../_references_/10-internal-storage/wiki-architecture.md) — six categories and articulation.

## Layout

**Core (00-02)** — foundational, change infrequently. **MOCs (03-20)** — evolving Maps of Content that link concerns together.

| # | Document | Covers | README |
|---|----------|--------|--------|
| 00 | [product-vision](00-product-vision.md) | vision, output, long-term loop | §1, §3, §30 |
| 01 | [principles](01-principles.md) | principles, core invariants, non-goals | §2, §28, §29 |
| 02 | [domain-model](02-domain-model.md) | entities, categories, frontmatter | §10, §28 |
| 03 | [vault](03-vault.md) | raw/wiki/sessions/output, Git ledger | §6, §10, §27 |
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

## Reading Order

1. **Understand the product**: 00 → 01 → 02.
2. **Build the knowledge platform**: 03 → 04 → 05 → 06.
3. **Build specification generation**: 07 → 08 → 09.
4. **Add governance**: 10 → 11.
5. **Build interfaces & architecture**: 12 → 13 → 14 → 15.
6. **Cross-cutting**: 16 → 17 → 18 → 19 → 20.

## Conventions

- Every doc has YAML frontmatter with a stable `id`, `layer` (core|moc), `lifecycle` (draft|review|approved), and a `traceability` block pointing back to README sections and references.
- Cross-references use Obsidian `[[wikilinks]]` (e.g. `[[10-risk-engine]]`).
- Each doc ends with **Acceptance Criteria**; [20-testing](20-testing.md) aggregates the Core Invariants into a test matrix.

## Status

All documents are `lifecycle: draft`. Advance them via [08-specification-lifecycle](08-specification-lifecycle.md) as they are reviewed and approved.
