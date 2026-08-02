# Provider Model

Providers execute Capabilities. They are **completely interchangeable** and
expose a common contract. Providers should never contain business logic.

```
Capability (stable)  →  Provider (interchangeable)
```

---

## Examples

```
OpenAI
Anthropic
Google Gemini
GitHub Copilot
Cursor
Claude Code
Human
Slack MCP
GitHub MCP
Temporal Activity
```

Note: **Human** is a Provider. Any external "agent" is modeled as a Provider —
"Agent" is not a separate domain concept (see
[../overview/glossary.md](../overview/glossary.md)).

---

## Provider Contract

Every Provider implements:

```
supports(capability)       → bool          # can it fulfill this capability?
estimate(capability, input) → Estimate     # cost/time/confidence (optional)
execute(capability, input, context) → ProviderResult
cancel(providerExecutionId)
resume(providerExecutionId, input)          # for paused/long-running runs
```

- `execute` is the only required behavior for MVP.
- `estimate` supports future cost/latency-aware strategies.
- `cancel` / `resume` support long-running and human-in-the-loop flows.

---

## Provider Definition

```
Provider {
  id
  name
  type                 # llm | mcp | human | activity
  supportedCapabilities[]
  config               # endpoints, model ids, limits
  credentialRef        # secret reference (never inline secrets)
}
```

Providers, credentials, and config are owned by the Catalog context at
Portfolio/Workspace level. See
[../domain/bounded-contexts.md](../domain/bounded-contexts.md).

---

## Selection

The concrete Provider for a Capability Execution is chosen **at runtime** by the
Execution Strategy, from the Capability's `supportedProviders` intersected with
the Portfolio's configured Providers.

- **MVP:** the single configured/default Provider for the Capability.
- **Future:** strategy-driven selection (parallel, consensus, cost-aware).

Capabilities remain stable while Providers change over time.

---

## Credentials & Security

- Providers reference credentials by secret reference; secrets are never stored
  in planning or events.
- Provider config is validated at the system boundary.
- See [../auth/auth.md](../auth/auth.md) and
  [../permissions/permissions.md](../permissions/permissions.md).

---

## Invariants

1. A Provider contains no business logic — only capability fulfillment.
2. Providers are interchangeable; swapping a Provider must not change planning or
   the Capability contract.
3. Provider Execution is the only place engine/LLM/MCP specifics live in the
   runtime; nothing above it depends on a concrete Provider.
