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

> Layout differences vs. the remote source (top-level `source/`, per-vault templates) are recorded in [[03-vault-contradiction]]. Local is authoritative.

## 0. Multi-Vault (Constitution P13)

The assistant supports **multiple vaults** under a configurable root:

- Default root `Vaults/`; each vault at `Vaults/<vault-name>/`.
- Overridable via environment: `LEADER_VAULT_ROOT` (root dir), `LEADER_VAULT_PATH` (explicit single-vault path), `LEADER_DEFAULT_VAULT` (default selector).
- Every capability resolves a target vault from an explicit selector, or the configured default when omitted ([[13-api]], [[14-chat]]).
- All durable state for a vault stays inside that vault. **Output templates are the exception** — they live in an externalized repo-root `templates/` shared across vaults (§5b).

## 1. Top-Level Layout

```text
Vaults/<vault-name>/
├── raw/         # immutable sources (never modified)
├── wiki/        # LLM workspace — all durable knowledge
├── sessions/    # operational conversations (short-term)
└── output/      # generated artifacts (reports, query results)

templates/       # repo-root, externalized, shared output templates (NOT inside a vault)
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

Reports, query results, exported deliverables. May feed back into knowledge via [[15-integrations]] §Output→Knowledge. Produced by reusing templates from the root `templates/` folder (§5b, [[21-outputs]]).

## 5b. `templates/` — Externalized Output Templates (repo root)

Reusable **output** structures (meeting summary, doc review, engineering ticket, strategy, project summary) live in a **repo-root `templates/` folder outside any vault**, so humans can review and evolve them independently (Constitution P7). The assistant reads them first (reuse-before-create) and proposes new templates only on no-match. See [`templates/README`](../templates/README.md) and [[21-outputs]]. Whether a new vault inherits copies is open — [[001-leader-assistant/plan-tbd|plan-tbd]] TBD-5.

## 6. Special Files

- `wiki/portal.md` — one line per page (`- [[page|Page]] — summary`, <120 chars), grouped by category. Updated on every ingest. See [[17-observability]].
- `wiki/log.md` — append-only entries `## [YYYY-MM-DD] operation | Title`. Never edit existing entries.

## 7. Git as Ledger

Every mutation is committed: raw ingestion metadata, source creation/updates, concept create/modify/delete, specification changes, conversation capture, generated artifacts. Git provides history, diffs, branches, rollback, review, merge. See [[11-git-workflow]].

## 8. Acceptance Criteria

- AC1: The four top-level directories exist (per vault) with the roles above; the repo-root `templates/` folder exists outside any vault.
- AC2: No process ever writes to files under `raw/`.
- AC6: A vault is resolvable by selector or default; `LEADER_VAULT_ROOT`/`LEADER_VAULT_PATH`/`LEADER_DEFAULT_VAULT` are honored (P13).
- AC3: `portal.md` reflects every wiki page after an ingest.
- AC4: `log.md` is strictly append-only (enforced/verified).
- AC5: The provenance chain in [[02-domain-model]] §5 is reconstructable for any wiki concept.
