# Template: Component Page

Copy this template to `wiki/resources/components/{component-name}.md` and fill in placeholders.

Use this for internal system components that deliver value to users — services, UI components, internal tools.

---

```markdown
---
Category: resources/components
Tags: [{pillar}, {domain}, {technology}]
Source links:
  - [[{source-link}]]
Created: {YYYY-MM-DD}
Last Updated: {YYYY-MM-DD}
---

# {Component Name}

{One-paragraph description of what this component does and its purpose.}

## Pillar

**{Pillar Name}** — {Brief explanation of how this component fits the pillar.}

{Pillar options: Serving, Ingestion, Management, Observability, Platform, etc.}

### Use Cases {optional}

Primary audience persona: [[{persona-link}|{Persona Name}]]

Used for:
- [[{feature-1}|{Feature Name}]] — {Brief context}
- [[{feature-2}|{Feature Name}]] — {Brief context}
- {Use case without dedicated feature page}

## Capabilities

### Purpose

- {Primary capability 1}
- {Primary capability 2}
- {Primary capability 3}

### Details {optional}

| Capability | Description |
|------------|-------------|
| **{Capability 1}** | {Description} |
| **{Capability 2}** | {Description} |
| **{Capability 3}** | {Description} |

## Integration

```
{ASCII architecture diagram showing component relationships}

┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  {Upstream}  │────▶│ {This Component}│────▶│ {Downstream} │
└──────────────┘     └─────────────────┘     └──────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │  {Dependency}   │
                     └─────────────────┘
```

### Endpoints {optional}

{If applicable — API endpoints exposed by this component}

Protected by [[{protection-mechanism}|{Mechanism Name}]]:
- `{endpoint-1}` — {Description}
- `{endpoint-2}` — {Description}

### Upstream {optional}

| Consumer | Purpose |
|----------|---------|
| [[{component}]] | {How they use this component} |
| [[{component}]] | {How they use this component} |

### Dependencies {optional}

| Component | Purpose | Dependency |
|-----------|---------|------------|
| [[{dependency-1}]] | {Purpose} | **Hard** |
| [[{dependency-2}]] | {Purpose} | **Soft** |

{Dependency types:}
- **Hard** — Component cannot function without this
- **Soft** — Component degrades gracefully without this

## Configuration

{If applicable — key configuration options}

| Setting | Default | Description |
|---------|---------|-------------|
| `{setting-1}` | `{default}` | {Description} |
| `{setting-2}` | `{default}` | {Description} |

## Operations

{If applicable — operational considerations}

### Monitoring

- **Key metrics:** {Metrics to watch}
- **Alerts:** {Critical alert conditions}
- **Dashboard:** {Link or reference}

### Scaling

- **Horizontal:** {How to scale horizontally}
- **Vertical:** {Resource requirements}

## Related

- [[{feature}|{Feature Name}]] — Feature this component powers
- [[{pattern}|{Pattern Name}]] — Pattern this component implements
- [[{dependency}|{Dependency Name}]] — Key dependency
- [[{sibling-component}|{Sibling Name}]] — Related component
```

---

## Minimal Component Page

For simpler components or initial documentation:

```markdown
---
Category: resources/components
Tags: [{pillar}, {domain}]
Source links:
  - [[{source-link}]]
Created: {YYYY-MM-DD}
Last Updated: {YYYY-MM-DD}
---

# {Component Name}

{One-paragraph description.}

## Purpose

- {Capability 1}
- {Capability 2}

## Integration

```
{Simple diagram}
```

### Dependencies

| Component | Purpose | Dependency |
|-----------|---------|------------|
| [[{dependency}]] | {Purpose} | **Hard** |

## Related

- [[{related-page}|{Name}]] — {Context}
```
