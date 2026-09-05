---
id: 202608152112-11
title: Git Workflow
spec: 11-git-workflow
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [git, ledger, branching, commits, review]
traceability:
  readme: ["§6 Git as the Knowledge and Specification Ledger", "§23 Git Workflow"]
  references: ["_references_/10-internal-storage/wiki-schema.md#git-as-memory"]
related:
  - "[[03-workspace]]"
  - "[[10-risk-engine]]"
  - "[[08-specification-lifecycle]]"
  - "[[17-observability]]"
Created: 2026-08-15
Last Updated: 2026-08-15
---

# Git Workflow

The Workspace is a Git repository; Git is the authoritative change history and the technical mechanism behind every mutation.

## 1. Normal (safe) Change

```text
change → risk evaluation → safe → commit main
```

## 2. Risky Change

```text
change → risk evaluation → risky → feature/{feature-name}
  → commit(s) → review → merge
```

The assistant MUST NOT silently merge a risky branch without the appropriate approval policy being satisfied.

## 3. What Gets Committed

Every meaningful mutation (README §6): raw ingestion metadata, source creation/updates, concept create/modify/delete, specification changes, conversation capture, generated artifacts.

## 4. Commit Message Convention (wiki-schema §Git as Memory)

Include:
- **Operation type**: `ingest`, `update`, `lint`, `synthesis`, `dreaming`, `spec`.
- **Affected pages**.
- **Source reference** if applicable.

Example: `ingest: add [[kafka]] + update [[idempotency]] (source: vault/raw/docs/kafka-guide.pdf)`.

## 5. Branch Naming

- `main` — safe, committed changes.
- `feature/{feature-name}` — risky changes isolated for review, per [[10-risk-engine]] output.

## 6. Relationship to Semantic Lifecycles

Git lifecycle backs but does not equal the specification lifecycle ([[08-specification-lifecycle]]) or the concept status lifecycle ([[05-zettelkasten]]). Diffs/branches are the technical substrate; `lifecycle`/`status` frontmatter carry the semantic state.

## 7. Acceptance Criteria

- AC1: Every knowledge/spec mutation results in a commit with the convention above.
- AC2: Safe changes commit to `main`; risky changes go to `feature/{feature-name}`.
- AC3: Risky branches merge only after the approval policy is satisfied.
- AC4: `vault/wiki/log.md` entries correlate with commits for auditability.
- AC5: The Workspace remains software-independent (plain Markdown + Git).
