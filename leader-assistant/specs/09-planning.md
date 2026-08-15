---
id: 202608132112-09
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
Created: 2026-08-13
Last Updated: 2026-08-13
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

## 5. Acceptance Criteria

- AC1: Explicit work requests produce a presented plan before execution.
- AC2: The user can critique and the assistant revises before executing.
- AC3: Clarifying questions are asked only when ambiguity is material; assumptions are otherwise stated explicitly.
- AC4: Routine autonomous operations (ingest, lint, dreaming) proceed without a plan.
- AC5: External or destructive actions never proceed without user approval.
