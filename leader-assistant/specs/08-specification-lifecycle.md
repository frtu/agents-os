---
id: 202608132112-08
title: Specification Lifecycle & Review
spec: 08-specification-lifecycle
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [lifecycle, review, approval, git]
traceability:
  readme: ["§5 Specification Lifecycle", "§24 Specification Review"]
  references: ["_references_/10-internal-storage/wiki-schema.md#git-as-memory"]
related:
  - "[[07-specification-model]]"
  - "[[09-planning]]"
  - "[[10-risk-engine]]"
  - "[[11-git-workflow]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# Specification Lifecycle & Review

Specifications have a **semantic** lifecycle, distinct from (but related to) the Git lifecycle.

## 1. States

```text
draft ──review──► review ──approve──► approved ──proposed change──► draft
```

Future states may be added: `superseded`, `deprecated`, `rejected`.

| State | Meaning | Who sets it |
|-------|---------|-------------|
| `draft` | continuous assistant generation | assistant |
| `review` | user is reviewing | user action |
| `approved` | user has approved | user action |

## 2. Semantic vs Git Lifecycle

```text
Specification lifecycle  +  Git lifecycle
```

The `lifecycle` frontmatter field carries the semantic state. Git independently provides history, diffs, branches, commits, rollback, review, and merge. They are **related but not identical** — a draft may span many commits; an approval is a semantic event backed by a specific commit.

## 3. Approved-Spec Protection (invariant)

Future assistant changes to an **approved** specification MUST create a new proposed revision rather than silently replacing the approved state:

```text
Approved Specification
   │ new knowledge
   ▼
Proposed Revision → Draft → Review → Approved
```

Git history provides the exact underlying changes. This maps to [[10-risk-engine]] rule `MODIFY_APPROVED_SPEC`.

## 4. Interaction with Continuous Generation

Because generation is continuous ([[07-specification-model]]), drafts change frequently. Users review "when ready," not when each spec is first created. The assistant surfaces pending changes via Git diffs and portal/log entries ([[17-observability]]).

## 5. Acceptance Criteria

- AC1: Each spec carries a `lifecycle` field reflecting its semantic state.
- AC2: Transitioning `draft→review→approved` is an explicit user action.
- AC3: Editing an `approved` spec never overwrites it silently — a new revision (draft) is opened, gated by `MODIFY_APPROVED_SPEC`.
- AC4: Semantic state and Git state are independently queryable and reconcilable.
- AC5: Every lifecycle transition is recorded in `vault/wiki/log.md` and Git.
