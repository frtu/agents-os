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

### 3.1 Low-friction turn flow ([[009-approval-optimization]])

A turn interrupts the user **only** when an executable `approval`-tier capability is about to run:

```text
User message → resolve the action this turn would execute
  ├── no executable action ──► normal answer (explain/advise) — no plan, ever
  ├── tier auto / reversible ──► run now; log + commit (undo = one git revert)
  └── tier approval ──► trust mode on?  ── yes ──► run now; log + commit
                                          └─ no ──► real plan (capability, target, tier, undo)
                                                     → approve → execute exactly that action
```

`ChatRequest` gains **`auto_approve: bool | null`** — `true`/`false` override the persisted trust
setting for that turn only, omitted uses the persisted default (009 FR-7/FR-9). The assistant never
raises an approval it cannot execute (009 FR-4), so AC3 below applies to executable approval-tier
work; the approval gate is produced **only** by the capability layer, while the agent may raise
clarification/notification cards ([[008-agent-user-interaction]] FR-18) but never approval.

### 3.2 In-turn grant for agent-raised approvals ([[010-agent-approval-channel]])

The agent also judges some work consequential that no capability resolver flags. It now asks through
a governed channel instead of prose, and the same trust check decides the outcome **before the turn
returns**:

```text
Agent judges its next step consequential → request_approval (tool)
  └── trust mode on?  ── yes ──► resolved "approved on your behalf" in-turn
      │                          → agent continues intermediate step → final execution
      │                          → surfaced as an inert resolved card + log entry
      └─ no ──────────────────► blocking approval card; tool says stop, nothing runs
                                 → human approves → **turn resumes** and completes the work
```

Two properties matter for the turn flow: with trust on there is **no round trip** (one turn does the
whole job, 010 FR-4), and with trust off approving **resumes** rather than acknowledging (010 FR-7).
A **clarification** is never auto-answered — standing consent can grant consent but cannot invent a
choice, so it blocks for the human regardless of trust mode (010 FR-8).

## 4. Acceptance Criteria

- AC1: Every chat exchange is persisted to `sessions/`.
- AC2: Chat exposes no capability absent from the API.
- AC3: Consequential requests show a plan before execution — refined by [[009-approval-optimization]]
  to *executable `approval`-tier* actions, and satisfiable instead by explicit operator standing
  consent (`auto_approve`), which keeps the action logged and revertible.
- AC4: Human judgments captured in chat influence knowledge maturity via dreaming/ingestion.
- AC5: Draft specs and alternatives are presented for feedback before finalization.
