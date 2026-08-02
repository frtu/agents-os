# Permissions

> MVP-depth spec. Authorization model kept minimal now; the enforcement point is
> fixed so richer roles are additive later.

Permissions decide **what** an authenticated User may do. Authentication is in
[../auth/auth.md](../auth/auth.md).

---

## Protected Operations

Per the Security NFR, only authorized Users may:

- start executions (`StartStory`, `StartTask`, `RetryExecution`)
- approve/submit decisions (`Approve`, `Reject`, `Clarify`, `Continue`, `Abort`,
  `SelectOption`)
- cancel workflows (`CancelExecution`)
- manage the Catalog (Capabilities, Providers, credentials)

Read/monitor operations (board, timeline, artifacts) are available to all
Portfolio members.

---

## MVP Model

- Two roles: **Leader** (full command access) and **Viewer** (read-only).
- Enforcement happens in the **application layer** (command handlers), not only
  the UI — the UI merely hides unavailable actions.

```
Command → AuthZ check (role) → Handler
```

---

## Auditability

Every authorized action is recorded with user, timestamp, execution, and reason
in the immutable event log — satisfying the Auditability NFR. Denials are logged
as `System` events.

---

## Future

- Fine-grained roles (Planner, Approver, Operator)
- Per-Initiative and per-Capability permissions
- Approval policies (e.g. budget over a threshold requires a specific role)
- Delegation and on-behalf-of execution

Owned by the Identity & Access bounded context — see
[../domain/bounded-contexts.md](../domain/bounded-contexts.md).
