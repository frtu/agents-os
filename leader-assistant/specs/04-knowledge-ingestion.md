---
id: 202608132112-04
title: Knowledge Ingestion
spec: 04-knowledge-ingestion
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [ingestion, pipeline, event-driven, provenance]
traceability:
  readme: ["§8 Automatic Ingestion", "§12 Knowledge Operations", "§13.1 Knowledge Ingestion Pipeline", "§20 Ingestion Engine"]
  references: ["_references_/10-internal-storage/wiki-schema.md#operations"]
related:
  - "[[03-vault]]"
  - "[[05-zettelkasten]]"
  - "[[10-risk-engine]]"
  - "[[11-git-workflow]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# Knowledge Ingestion

Ingestion is **event-driven**: any new document stored anywhere under `vault/raw/` automatically starts ingestion. The user should never need to say "process this file."

> This spec describes the **local** two-stage pipeline (`vault/raw → sessions → dreaming → vault/wiki/sources → vault/wiki/category`). The remote source uses a flatter `raw → source → wiki` model; the divergence is recorded in [[04-knowledge-ingestion-contradiction]]. Local is authoritative. Concept creation/update here writes the lifecycle counter/reference fields (`usage-count`, `referenced-to`, `last-correction`) per [[05-zettelkasten]].

## 1. Trigger

```text
vault/raw/{any-path}/{document}
              │
              ▼
       ingestion trigger
```

Includes arbitrary subdirectories (`vault/raw/articles/`, `vault/raw/zoom/`, `vault/raw/voice/`, `vault/raw/imported/`, …). The implementation MUST watch `vault/raw/` recursively for created/updated files.

## 2. Pipeline

```text
New raw document
   │
   ▼
Detect / classify (source type)
   │
   ▼
Read source (completely)
   │
   ▼
Normalize
   │
   ▼
Create/update source summary  → vault/wiki/sources/{provenance}/{source}.md
   │
   ▼
Compare with existing wiki
   ├── Existing knowledge   (update pages)
   ├── New knowledge        (create pages)
   ├── Contradiction        (flag, cite both)
   └── Uncertainty          (mark, lower confidence)
   │
   ▼
Generate proposed wiki mutations
   │
   ▼
Risk evaluation ──► safe: commit to main
                └─► risky: feature/{feature-name}
   │
   ▼
Update portal.md + append log.md
```

## 3. Operational Rules (from wiki-schema §Ingest)

1. Read the source completely; discuss key takeaways with the user where interactive.
2. Create a **source summary** in `vault/wiki/sources/{provenance}/` (title, source metadata, key claims, structured summary). Keep it factual — save interpretation for concept/synthesis pages.
3. Categorize content into the right subdirectories (product / people / concepts / resources). See [[02-domain-model]] and the wiki-architecture decision flowchart.
4. For each topic: update the existing page if present, else create one in the most specific subfolder.
5. **Knowledge-transfer rule**: final category pages contain standalone knowledge; they reference source summaries but never sessions or daily digests directly.
6. Add `[[wikilinks]]` between all related pages, stating *why* each link exists.
7. Update `vault/wiki/portal.md`; append `## [YYYY-MM-DD] ingest | Source Title` to `vault/wiki/log.md`.

A single source may touch 10–15 wiki pages — that is normal.

## 4. Ingestion Engine Responsibilities (README §20)

detect raw documents · classify source type · normalize · generate source documents · extract knowledge candidates · compare against existing knowledge · generate wiki changes · invoke risk evaluation · commit or branch.

## 5. Continuous Specification Coupling

A knowledge change can propagate into specifications automatically (see [[07-specification-model]] §Continuous Generation and [[16-workflows]]):

```text
New source → ingestion → new concept → project relevance detected
  → specification impact analysis → draft specification update
```

## 6. Acceptance Criteria

- AC1: Dropping a file anywhere under `vault/raw/` triggers ingestion without a manual command.
- AC2: Every ingested source yields exactly one source summary under the mirrored `{provenance}` path.
- AC3: Contradictions are recorded with both sources cited.
- AC4: Every ingest updates `portal.md` and appends one `ingest` log entry.
- AC5: Proposed mutations pass through [[10-risk-engine]] before landing on `main`.
