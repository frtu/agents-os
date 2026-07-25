# /specs/frontend.md

# Frontend

## Design Goals

The UI optimizes for supervision rather than editing.

The leader should answer:

- What is running?
- What needs me?
- What completed?
- Where are we blocked?

within seconds.

---

# Primary Views

## Kanban

Stories grouped by Epic.

Columns

- Todo
- Ready
- Running
- Blocked
- Completed

---

## Story Detail

Displays

Planning

Timeline

Tasks

Artifacts

Execution

Human Requests

---

## Task Detail

Displays

Execution history

Agent status

Logs

Produced artifacts

Waiting reason

---

## Attention Queue

Central inbox for all Human Requests.

Sorted by

Priority

Waiting Time

Story

Execution

---

## Notifications

Transient updates.

Examples

Execution completed

Approval required

Workflow failed

Artifact generated

---

# State Management

Server State

TanStack Query

Local UI State

Zustand

Realtime

WebSocket

---

# Offline Behaviour

UI remains usable during temporary connection loss.

Server synchronization resumes automatically.
