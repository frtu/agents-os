# Notifications

> MVP-depth spec.

Notifications surface **transient awareness** of events. They do **not** block
execution and do **not** require a Decision — that distinguishes them from
[Human Requests](../execution/human-requests.md).

| | Human Request | Notification |
| - | ------------- | ------------ |
| Blocks execution | Yes | No |
| Requires a Decision | Yes | No |
| Surfaced in | Attention Queue | Notifications panel |

---

## Sources

Notifications are a projection over selected domain events (see
[../domain/event-model.md](../domain/event-model.md)):

```
Execution completed
Approval required        (mirror of a Human Request, for awareness)
Workflow failed
Artifact generated
```

---

## Shape

```
Notification { id, userId, type, payload, read, createdAt }
```

Lifecycle: `Created → (Viewed) → Dismissed`.

---

## Delivery

- **MVP:** in-app only, pushed over WebSocket (`NotificationCreated`) and listed
  in the Notifications panel. See [../api/realtime.md](../api/realtime.md).
- **Future:** external channels (Slack, email) via Integrations; per-user
  preferences and digests.

---

## Requirements

1. A Notification never changes runtime state; it only informs.
2. Notifications are per-User read models; dismissing one does not affect others.
3. Critical items that require action are represented as Human Requests, not
   notifications alone.
