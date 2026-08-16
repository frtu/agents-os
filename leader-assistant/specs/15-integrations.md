---
id: 202608132112-15
title: External Integrations & Output Feedback
spec: 15-integrations
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [integrations, external-pm, feedback-loop, jira, linear]
traceability:
  readme: ["§16 External Project Management Systems", "§26 Output → Knowledge Feedback"]
  references: ["_references_/10-internal-storage/wiki-architecture.md"]
related:
  - "[[00-product-vision]]"
  - "[[09-planning]]"
  - "[[13-api]]"
  - "[[16-workflows]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# External Integrations & Output Feedback

The external PM system is an **integration boundary**, invoked only on explicit user demand. The assistant does not continuously synchronize its Vault with a PM system.

## 1. On-Demand External Actions

Examples: "Create a new story for payment reconciliation." · "Update the acceptance criteria of story ABC-123." · "Create these tasks in Jira." · "Move this ticket to In Progress."

Procedure (README §16):
1. understand the request;
2. use knowledge and specifications;
3. generate a proposed action/plan ([[09-planning]]);
4. ask for clarification if needed;
5. invoke the external integration;
6. capture the resulting output/action;
7. optionally feed useful resulting knowledge back into the Vault.

The Integration Manager ([[12-assistant]]) owns these boundaries.

## 2. Boundary Rules (invariants)

- The Vault is **not** the PM system (Jira, Linear, Azure DevOps). See [[00-product-vision]].
- No autonomous execution of arbitrary external actions without user intent ([[01-principles]] Non-Goals).
- No continuous whole-Vault synchronization with any PM tool.

> Producing the artifacts themselves (meeting summaries, tickets, strategy, etc.) — reusing the externalized root `templates/` — is the secondary output capability specified in [[21-outputs]]. This doc covers pushing them to external systems and feeding results back.

## 3. Output → Knowledge Feedback (README §26)

Generated artifacts can become inputs to the knowledge system:

```text
Knowledge → Specification → Review → Feedback → Improved Knowledge
```

After generating an output, evaluate: which concepts were used; whether existing concepts needed correction; whether new concepts emerged; whether a contradiction was discovered; whether the spec exposed missing knowledge; whether concept usage should be recorded (`referenced-to`, [[05-zettelkasten]]).

## 4. Acceptance Criteria

- AC1: External PM actions occur only when explicitly requested by the user.
- AC2: Each external action is preceded by a proposed action/plan.
- AC3: Results of external actions are captured (and optionally fed back into the Vault).
- AC4: No background process synchronizes the whole Vault to an external PM tool.
- AC5: Generated outputs trigger an output→knowledge evaluation recording concept usage.
