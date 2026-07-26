# Capability Model

Capabilities describe **what the platform can do**. They are stable business
concepts, intentionally independent from prompts, LLMs, providers, and execution
engines.

A Capability does **not** describe:

- prompts
- LLMs
- providers
- execution engines

---

## Capability Shape

```
Capability {
  id
  name
  description
  inputs               # typed input contract
  outputs              # typed output contract
  supportedProviders   # providers able to fulfill this capability
}
```

Example:

```
Capability
  Write Markdown
Inputs
  Markdown Specification
Outputs
  Markdown Document
```

---

## Capability Catalog

Capabilities are reusable across every Initiative and managed at
Portfolio/Workspace level.

```
Capability Catalog
  Research
  Search
  Review
  Write Markdown
  Generate Diagram
  Generate Presentation
  Generate Code
  Analyze
  Summarize
  Translate
  Test
  Deploy
  Review Architecture
```

The Catalog is the single registry that Structured planning selects from and
that the AI Planner draws from in Goal-Oriented mode.

---

## Capability vs Provider

| Concern | Owned by |
| ------- | -------- |
| *What ability is required* | **Capability** (stable) |
| *How it is executed* | **Execution Strategy** |
| *Who executes it* | **Provider** (interchangeable) |

A Capability lists `supportedProviders`, but the concrete Provider is chosen at
runtime by the Execution Strategy — never fixed at planning time. See
[../execution/providers.md](../execution/providers.md) and
[../execution/execution-strategy.md](../execution/execution-strategy.md).

---

## Lifecycle & Versioning

- Capabilities are Portfolio-managed catalog entries.
- Changing a Capability's input/output contract is a **new version**; existing
  planning references pin to a version for reproducibility.
- Adding a new supported Provider does not change the Capability version.

---

## Invariants

1. A Structured Task references exactly one Capability (by id + version).
2. A Capability is provider-independent; it must be fulfillable by at least one
   Provider.
3. Capability input/output contracts are typed and validated at the system
   boundary (see [../api/rest-api.md](../api/rest-api.md)).
