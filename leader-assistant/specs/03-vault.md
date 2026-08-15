---
id: 202608132112-03
title: Knowledge Vault
spec: 03-vault
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [vault, storage, git, directory-structure, provenance]
traceability:
  readme: ["§6 Git as the Knowledge and Specification Ledger", "§10 Knowledge Layers", "§27 Portal and Log"]
  references: ["_references_/10-internal-storage/wiki-schema.md#architecture", "_references_/10-internal-storage/wiki-architecture.md"]
related:
  - "[[02-domain-model]]"
  - "[[04-knowledge-ingestion]]"
  - "[[05-zettelkasten]]"
  - "[[11-git-workflow]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# Knowledge Vault

The Vault is a **Git repository of Markdown documents**. Every meaningful mutation is a Git commit. This spec defines its physical layout; [[04-knowledge-ingestion]], [[05-zettelkasten]], and [[06-conversations]] define how it is populated.

## 1. Top-Level Layout

```text
Vault/
├── raw/         # immutable sources (never modified)
├── wiki/        # LLM workspace — all durable knowledge
├── sessions/    # operational conversations (short-term)
└── output/      # generated artifacts (reports, query results)
```

## 2. `raw/` — Immutable Sources

Properties: provenance-preserving, immutable source of truth, ingestion-triggering, never treated as synthesized knowledge. The LLM reads but **never modifies** these files.

Canonical subdirectories:

- `raw/assets/` — images/audio referenced with `![[resource/path]]`.
- `raw/clippings/` — web articles (Obsidian Web Clipper or manual).
- `raw/docs/` — PDFs, papers, received reference files.
- `raw/notes/` — handwritten notes, briefs, ideas.
- `raw/transcripts/` — meeting/voice/interview transcripts.

Arbitrary subdirectories are allowed; all are ingestion candidates. The `{provenance}` subpath under `raw/` is preserved through the whole chain.

## 3. `wiki/` — Durable Knowledge Workspace

Six categories (see [[02-domain-model]] §2). Directory map:

```text
wiki/
├── sources/
│   ├── _daily_/                 # daily digests (dreaming output)
│   └── {provenance}/            # source summaries mirroring raw/
├── concepts/{patterns,technologies}/
├── product/{persona,entities,features}/
├── product/specs/               # the assistant's RUNTIME spec kit (00-02 core, 03+ MOCs)
├── people/{processes,steps,roles,competencies,members}/
├── resources/{artifacts,components,dependencies,tools}/
├── projects/{initiative}|{product}/{project}/
├── synthesis/
├── portal.md                    # master catalog (updated every ingest)
└── log.md                       # append-only operational record
```

> **Path note (README §32 precedence):** the assistant's runtime spec kit lives at `wiki/product/specs/` per wiki-schema, even though README §31 writes it as `wiki/specs/`. This build spec kit (the one you are reading) lives at the repo-level `specs/` and is separate.

Rule: always write into the **most specific** subfolder that fits; fall back to the parent only when none matches.

## 4. `sessions/` — Short-Term Memory

Ephemeral operational conversation logs. Not part of the wiki. Feed the dreaming pipeline. See [[06-conversations]].

## 5. `output/` — Generated Artifacts

Reports, query results, exported deliverables. May feed back into knowledge via [[15-integrations]] §Output→Knowledge.

## 6. Special Files

- `wiki/portal.md` — one line per page (`- [[page|Page]] — summary`, <120 chars), grouped by category. Updated on every ingest. See [[17-observability]].
- `wiki/log.md` — append-only entries `## [YYYY-MM-DD] operation | Title`. Never edit existing entries.

## 7. Git as Ledger

Every mutation is committed: raw ingestion metadata, source creation/updates, concept create/modify/delete, specification changes, conversation capture, generated artifacts. Git provides history, diffs, branches, rollback, review, merge. See [[11-git-workflow]].

## 8. Acceptance Criteria

- AC1: The four top-level directories exist with the roles above.
- AC2: No process ever writes to files under `raw/`.
- AC3: `portal.md` reflects every wiki page after an ingest.
- AC4: `log.md` is strictly append-only (enforced/verified).
- AC5: The provenance chain in [[02-domain-model]] §5 is reconstructable for any wiki concept.
