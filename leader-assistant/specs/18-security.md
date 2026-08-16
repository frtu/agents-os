---
id: 202608132112-18
title: Security & Safety
spec: 18-security
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [security, safety, immutability, human-control, provenance]
traceability:
  readme: ["§2.2 Raw information is preserved", "§2.4 Human remains in control", "§7 Risk-Based Branching", "§16 External PM Systems", "§29 Initial Non-Goals"]
  references: ["_references_/10-internal-storage/wiki-schema.md#rules"]
related:
  - "[[01-principles]]"
  - "[[10-risk-engine]]"
  - "[[15-integrations]]"
  - "[[11-git-workflow]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# Security & Safety

Security here is primarily about **data integrity, provenance, and controlled autonomy** rather than a public attack surface. It derives from the product principles and invariants.

## 1. Raw Immutability

Files under `vault/raw/` are never modified or deleted by the assistant (wiki-schema Rule 1). This preserves provenance and the source of truth. Enforcement: writes to `vault/raw/` are rejected; verified by tests ([[20-testing]]).

## 2. Human Control of Consequential Work

- Consequential/destructive work requires a plan + approval ([[09-planning]]).
- External actions occur only on explicit user demand ([[15-integrations]]).
- No autonomous execution of arbitrary external actions ([[01-principles]] Non-Goals).

## 3. Risk Gating

Potentially destructive or high-impact mutations are caught by the risk engine ([[10-risk-engine]]) and routed to feature branches for review; risky branches never auto-merge.

## 4. Provenance Integrity

Every processed source retains provenance; the chain `vault/raw → sources → vault/wiki` must be intact and auditable ([[17-observability]]). Low-provenance changes are flagged (`LOW_PROVENANCE_CONFIDENCE`).

## 5. Secrets & Sensitive Content

- Do not ingest or commit secrets/credentials found in raw material into wiki pages; flag and exclude.
- Treat external integrations' credentials as configuration outside the Vault; never persist them in Markdown.
- Before sending content to external tools, consider sensitivity (it may be cached/indexed).

## 6. Auditability

Every mutation is a Git commit with an operation-typed message ([[11-git-workflow]]); `vault/wiki/log.md` is append-only. Together they form a tamper-evident record.

## 7. Acceptance Criteria

- AC1: No code path writes to `vault/raw/`.
- AC2: Destructive/consequential actions require explicit approval.
- AC3: External actions never fire autonomously.
- AC4: Secrets in raw material are never propagated into wiki pages or commits.
- AC5: Every mutation is attributable via Git + log.
