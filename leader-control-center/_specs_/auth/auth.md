# Authentication

> MVP-depth spec. Scope grows with the roadmap; the boundary (Identity & Access
> context) is fixed now so later expansion is additive.

Authentication establishes **who** is acting. Authorization (**what** they may
do) is in [../permissions/permissions.md](../permissions/permissions.md).

---

## MVP

- Single Portfolio, small set of trusted Users.
- Session-based auth (token issued on login) carried on REST and WebSocket.
- Users belong to one Portfolio; identity is attached to every command as
  `actor` for the audit trail (see
  [../domain/event-model.md](../domain/event-model.md)).

```
User → Login → Session Token → REST + WebSocket
```

---

## Requirements

1. Every mutating command is attributable to an authenticated User.
2. The WebSocket connection is authenticated at handshake; unauthenticated
   sockets are rejected.
3. Provider credentials are **never** user-visible; they are referenced by secret
   ref only (see [../execution/providers.md](../execution/providers.md)).

---

## Future

- OIDC / SSO integration
- Multiple Portfolios with per-Portfolio membership
- Service accounts for automation (AI Planning, scheduled runs)
- Token refresh + revocation

Identity is owned by the Identity & Access bounded context — see
[../domain/bounded-contexts.md](../domain/bounded-contexts.md).
