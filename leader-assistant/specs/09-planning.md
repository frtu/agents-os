---
id: 202608152112-09
title: Planning-First Interaction & Clarification
spec: 09-planning
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [planning, clarification, interaction-model, human-in-the-loop]
traceability:
  readme: ["§2.4 Human remains in control", "§14 Planning-First User Interaction", "§15 Clarification Behavior"]
  references: []
related:
  - "[[01-principles]]"
  - "[[07-specification-model]]"
  - "[[10-risk-engine]]"
  - "[[16-workflows]]"
Created: 2026-08-15
Last Updated: 2026-08-15
---

# Planning-First Interaction & Clarification

The assistant does not jump from request to large-scale execution. Consequential work starts with a plan the user can criticize.

## 1. Interaction Model

```text
User Request → Knowledge Retrieval → Plan → User Review
  ├── Critique ──► Revised Plan
  └── Approve ──► Execute → Draft Output → User Feedback → Final Output
```

## 2. Planning Procedure (README §14)

For an explicit work request the assistant SHALL:
1. understand the request;
2. inspect relevant Vault knowledge;
3. identify missing information;
4. ask clarification questions if needed;
5. produce a complete plan;
6. present the plan;
7. allow the user to criticize it;
8. revise the plan;
9. execute it;
10. produce draft specification documents;
11. present meaningful alternatives where necessary;
12. incorporate feedback.

## 3. Clarification Behavior (README §15)

Ask clarification when ambiguity materially affects: project scope, specification structure, business requirements, architecture, external actions, destructive changes, knowledge classification, risk evaluation, or output expectations.

Do **not** ask unnecessary questions when reasonable assumptions can be safely made. When assumptions are made, state them explicitly.

## 4. Autonomy Boundary

Autonomous without a plan: ingestion, analysis, synthesis, draft generation, knowledge maintenance. Requires a plan + review: substantial/consequential work, external actions ([[15-integrations]]), and anything the [[10-risk-engine]] marks risky.

### 4.1 Refinement — effect-based, executable-only planning ([[009-approval-optimization]])

The boundary is drawn by the **effect the capability about to run declares**, not by the wording of the request:

- A plan is produced **only** for an **executable** capability of effect tier `approval` (destructive, irreversible-outside-git, or external). `auto` and `reversible` tiers proceed unprompted — reversible work is git-committed, so review happens after the fact by revert.
- A request that maps to **no executable capability** gets a **direct answer**, never a plan. The assistant never asks for an approval it cannot honor (009 FR-4).
- A plan names the **actual** capability, its target, effect tier, and undo path (009 FR-5); boilerplate plans are non-conforming.
- The operator may grant **standing consent** (trust mode / `auto_approve`), which replaces per-action review while keeping every action logged and revertible (Constitution P8). AC1/AC5 below are satisfied by per-action review, standing consent, **or** the bounded checker of §4.3.
- **Superseded in part by [[011-maker-checker-approval]]:** the "capability about to run" is no longer resolved from the **request text**. 011 FR-2/FR-6 moves the boundary to the operation each layer **announces as it attempts it** — including the agent's native tools — so the executable-only and no-dead-end rules above still hold, but the resolution step they were built on is gone.

### 4.2 The agent's own judgment has a channel ([[010-agent-approval-channel]])

§4.1 draws the boundary for the **deterministic** resolver. The assistant also forms its own view of what deserves consent — for work no resolver flags — and that judgment now has a governed home:

- It **requests** approval through a tool; the request becomes a real interaction (id, one proposal, countdown, durable record, resolution event), never a prose "reply approve" (010 FR-1). Asking in prose is a defect, because such an approval is invisible to trust mode, the UI and the audit trail.
- It never **grants for itself**: the outcome comes from the human, from the operator's standing consent, or from the **bounded checker** of [[011-maker-checker-approval]] (FR-17) — a separate party with no execution capability, whose `approve` is honoured only by deterministic code and only under standing consent or recorded precedent, and which fails closed to asking (Constitution P8 v2.0.0). With trust on the grant is issued in-turn so the work completes without a round trip (010 FR-4); with trust off nothing runs until the human answers, and answering **resumes** the work (010 FR-7).
- The judgment is formed over the **whole execution** a request causes, not one resolved action: the accumulated, scored operation list of 011 FR-11 is what the checker weighs and what the operator is shown.
- §3 still governs restraint. This channel is for **consent**, not for questions the assistant could answer itself — an unnecessary approval card is the same defect as an unnecessary clarifying question (AC3 below). A genuine choice between distinct approaches remains a **clarification**, which standing consent can never answer (010 FR-8).

## 5. Acceptance Criteria

- AC1: Explicit work requests produce a presented plan before execution.
- AC2: The user can critique and the assistant revises before executing.
- AC3: Clarifying questions are asked only when ambiguity is material; assumptions are otherwise stated explicitly.
- AC4: Routine autonomous operations (ingest, lint, dreaming) proceed without a plan.
- AC5: External or destructive actions never proceed without user approval.
