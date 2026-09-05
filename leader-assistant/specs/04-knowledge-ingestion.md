---
id: 202608152112-04
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
  - "[[03-workspace]]"
  - "[[05-zettelkasten]]"
  - "[[10-risk-engine]]"
  - "[[11-git-workflow]]"
Created: 2026-08-15
Last Updated: 2026-08-15
---

# Knowledge Ingestion

> This spec describes the **local** two-stage pipeline (`vault/raw → sessions → dreaming → vault/wiki/sources → vault/wiki/category`). The remote source uses a flatter `raw → source → wiki` model; the divergence is recorded in [[04-knowledge-ingestion-contradiction]]. Local is authoritative. Concept creation/update here writes the lifecycle counter/reference fields (`usage-count`, `referenced-to`, `last-correction`) per [[05-zettelkasten]].

## 0. Capture vs Ingest

Two distinct steps, deliberately separated (Constitution P2; README § Core Concepts):

- **Capture** — an *input mechanism only*. It deposits a human-provided source into
  `vault/raw/<provenance>/` and performs **no processing**. Channels: UI upload, API upload,
  or the assistant depositing on a human's behalf ([[004-assistant-sidebar]]). Capture never
  derives knowledge; it just makes a source *exist* in `raw/`, ready to be ingested.
- **Ingest** — the internal **workflow** that reads *captured* sources and derives durable
  knowledge (`vault/raw/ → vault/wiki/`). Everything in §2–§4 below is the ingest workflow.

Ingest is built **bottom-up** on a reusable **activity** — a skill (`second-brain-ingest`) run
headless behind a pydantic contract — that the app orchestrates but never modifies. The activity
interface, the `activity_ingest.py` wrapper, and the capture→ingest wiring are specified in
[[007-knowledge-activities]]. This MOC defines *what* the workflow must achieve; feature 007
defines *how* it is layered and invoked.

## 1. Trigger

Ingest runs over already-**captured** sources under `vault/raw/`. Two invocation modes:

- **On-demand (implemented target).** Ingest is invoked explicitly for a workspace (via the
  capability / API), scanning `vault/raw/` for unprocessed sources ([[007-knowledge-activities]]).
- **Event-driven (future).** A watcher observes `vault/raw/` and starts ingest automatically on
  a new/updated file, so the user never has to say "process this file."

```text
vault/raw/{any-path}/{document}   (captured, immutable)
              │
              ▼
       ingest workflow  (on-demand today; event-driven later)
```

Includes arbitrary subdirectories (`vault/raw/articles/`, `vault/raw/zoom/`, `vault/raw/voice/`, `vault/raw/imported/`, …). The event-driven mode MUST watch `vault/raw/` recursively for created/updated files.

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

- AC1: Ingest runs over captured sources under `vault/raw/`. On-demand invocation scans `vault/raw/`
  for unprocessed sources (implemented target); event-driven auto-trigger on file drop is the future
  extension ([[007-knowledge-activities]]).
- AC2: Every ingested source yields exactly one source summary under the mirrored `{provenance}` path.
- AC3: Contradictions are recorded with both sources cited.
- AC4: Every ingest updates `portal.md` and appends one `ingest` log entry.
- AC5: Proposed mutations pass through [[10-risk-engine]] before landing on `main`.
- AC6: Capture (input) never derives knowledge and ingest (workflow) never writes back into
  `vault/raw/` — the two steps stay separated (Constitution P2).
