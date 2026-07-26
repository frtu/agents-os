# Realtime API

Live supervision requires push updates. The primary transport is **WebSocket**,
with **Server-Sent Events** as a future fallback. Clients maintain synchronized
local state and reconcile with REST queries on reconnect.

---

## Transport

```
Client ⇄ WebSocket /api/v1/stream
```

- One connection per authenticated session.
- Subscriptions are scoped (Initiative, Story Execution, or global Attention).
- Messages are JSON with a `type` and `payload`.

---

## Subscriptions

```
{ "action": "subscribe", "topic": "initiative", "id": "..." }
{ "action": "subscribe", "topic": "execution", "id": "..." }
{ "action": "subscribe", "topic": "attention" }
{ "action": "unsubscribe", "topic": "...", "id": "..." }
```

---

## Server → Client Messages

Derived from domain events (see
[../domain/event-model.md](../domain/event-model.md)); provider/engine internals
are never sent.

```
StoryUpdated
ExecutionUpdated
TimelineUpdated
DecisionRequested
DecisionApplied
ArtifactProduced
AttentionUpdated
NotificationCreated
```

Each message carries the aggregate id, a `sequence`, and a minimal payload the
client uses to update its cache.

---

## Ordering & Reconnect

- Messages include a monotonic `sequence` per aggregate.
- On reconnect, the client sends the last seen `sequence`; the server replays
  missed messages or instructs a full refetch.
- If a gap cannot be filled, the client refetches the affected projection via
  REST (see [rest-api.md](./rest-api.md)).

---

## Client State Model

- **Server state:** TanStack Query cache, updated by WebSocket messages.
- **Realtime channel:** WebSocket subscription manager.
- **Offline:** UI stays usable during connection loss; sync resumes
  automatically. See [../frontend/frontend.md](../frontend/frontend.md).

---

## Invariants

1. Realtime messages are projections of events — never a second source of truth.
2. A dropped connection never loses data; REST reconciliation is authoritative.
3. The client never receives WorkflowId/RunId/Activity or provider secrets.
