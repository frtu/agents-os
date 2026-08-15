---
id: 202608132112-14
title: Chat Interface
spec: 14-chat
layer: moc
status: draft
lifecycle: draft
Category: spec
Tags: [chat, interface, parity, conversation]
traceability:
  readme: ["§17 API and Chat Parity", "§9 Conversation Capture", "§14 Planning-First User Interaction"]
  references: []
related:
  - "[[13-api]]"
  - "[[06-conversations]]"
  - "[[09-planning]]"
  - "[[12-assistant]]"
Created: 2026-08-13
Last Updated: 2026-08-13
---

# Chat Interface

The Application Chat is the human-facing surface over the same capability layer as the API. It is where planning, review, and clarification happen conversationally.

## 1. Parity Constraint

Chat must not implement capabilities that cannot be invoked through the API ([[13-api]]). Chat is a presentation of shared capabilities, not a separate implementation.

## 2. Conversational Responsibilities

- Capture every conversation to `sessions/` automatically ([[06-conversations]]).
- Surface plans for critique/approval per [[09-planning]].
- Present draft specifications and meaningful alternatives; incorporate feedback.
- Record human judgments (upvotes/downvotes, corrections) into sessions for later dreaming.

## 3. Human-in-the-Loop Flow

```text
User message → (ingest/query/plan) → assistant response
  → for consequential work: plan → review → execute → draft → feedback → final
```

Routine autonomous operations (ingest, lint, dreaming) may run without interrupting the chat, with results reflected in portal/log and Git.

## 4. Acceptance Criteria

- AC1: Every chat exchange is persisted to `sessions/`.
- AC2: Chat exposes no capability absent from the API.
- AC3: Consequential requests show a plan before execution.
- AC4: Human judgments captured in chat influence knowledge maturity via dreaming/ingestion.
- AC5: Draft specs and alternatives are presented for feedback before finalization.
