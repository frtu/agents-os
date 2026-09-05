---
id: 202608152112-18
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
Created: 2026-08-15
Last Updated: 2026-08-15
---

# Security & Safety

Security here is primarily about **data integrity, provenance, and controlled autonomy** rather than a public attack surface. It derives from the product principles and invariants.

## 1. Raw Immutability

Files under `vault/raw/` are never modified or deleted by the assistant (wiki-schema Rule 1). This preserves provenance and the source of truth. Enforcement: writes to `vault/raw/` are rejected; verified by tests ([[20-testing]]).

## 2. Human Control of Consequential Work

- Consequential/destructive work requires a plan + approval ([[09-planning]]).
- External actions occur only on explicit user demand ([[15-integrations]]).
- No autonomous execution of arbitrary external actions ([[01-principles]] Non-Goals).

### 2.1 Bounded delegation — blast radius of a compromised checker ([[011-maker-checker-approval]])

Constitution P8 v2.0.0 admits a **non-human checker** that can answer an approval on the operator's
behalf. That is a new trust boundary, so its failure modes are stated explicitly:

- The checker **cannot execute anything** (011 FR-22): no capability access, no tools, no filesystem
  writes except appending to the experience store. A compromised checker cannot perform an action; it
  can only influence whether the operator is asked.
- The checker **cannot widen its own authority**. Its `approve` passes through a **deterministic
  post-filter** (011 FR-17) that honours it only under the operator's standing consent or a matching
  recorded precedent, and refuses it above the precedent-free ceiling (FR-18). The filter is code the
  checker cannot reach.
- The checker **fails closed**: unavailable, timed out, malformed, or precedent-free resolves to
  **ask** (011 FR-20/FR-21). Its worst realistic outcome is therefore **asking more often**, which is
  a usability regression, not a security one.
- The checker **may not learn to refuse**. An autonomous `decline` is permitted only on the precedent
  of a prior operator decline for the same fingerprint (011 FR-19), so a compromised checker cannot be
  used to deny the operator service by fabricating refusals.
- **§1 is unconditional.** The `vault/raw/` prohibition is not a scored decision and no verdict, score
  or trust setting can satisfy it (011 AC-20).
- The experience store is **append-only and human-auditable**, and weights are hand-edited: a
  precedent match must be explainable without re-running the checker (011 FR-31), and no routine
  auto-applies a threshold change (011 FR-32).

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
- AC2: Destructive/consequential actions require explicit approval — from the operator, from their
  standing consent, or from a bounded checker within the limits of §2.1; every such decision records
  **which party decided**.
- AC3: External actions never fire autonomously.
- AC4: Secrets in raw material are never propagated into wiki pages or commits.
- AC5: Every mutation is attributable via Git + log.
