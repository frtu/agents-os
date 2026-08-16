# Template: Infrastructure Component Page

Copy this template to `wiki/resources/components/infra-{product}-{component-name}.md` and fill in placeholders.

**Naming convention:** `infra-{product}-{component-name}.md`
- `{product}` — the product/domain (e.g., `search`, `workflow`)
- `{component-name}` — the specific component (e.g., `service`, `facade`, `ingestion`, `management`, `engine`, ...)
- Examples: `infra-search-service.md`, `infra-search-facade.md`, `infra-search-ingestion.md`

Use this for **infrastructure deployment pages** — documenting topology, environments, regions, and URLs for components. These pages complement capability-focused component pages in other vaults (e.g., search vault) by focusing on deployment and infrastructure details.

---

```markdown
---
Category: resources/components
Tags: [component, infrastructure, {domain}, {product}]
Source links:
	- [[{source-link}]]
Created: {YYYY-MM-DD}
Last Updated: {YYYY-MM-DD}
---

# Infra {Component Name}

> **Note:** For component capabilities, integration details, and use cases, see the main [[Vault/{vault}/wiki/resources/components/{component}|{Component Name}]] page in the {vault} vault or more specifically {product}. This page documents deployment and infrastructure details only.

{One-line description of what this component is and its role in infrastructure.}

## Integration

{ASCII diagram showing component's position in the infrastructure topology.}

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

## Deployment

### Environments & URIs

| Environment | Regions | URI Pattern |
|-------------|---------|-------------|
| dev | {region} | `https://{service}.tp.gcp-{region}.dev.awx.im` |
| staging | {regions} | `https://{service}.tp.gcp-{region}.staging.awx.im` |
| demo | {region} | `https://{service}.tp.gcp-{region}.demo.awx.im` |
| prod | {regions} | `https://{service}.tp.gcp-{region}.prod.awx.im` |

{If deployment info is pending, use:}

> **TBD:** Cluster URLs and region deployments pending infrastructure documentation.

| Environment | Regions | Status |
|-------------|---------|--------|
| Dev | TBD | TBD |
| Staging | TBD | TBD |
| Production | TBD | TBD |

### Cluster Specifications

{If applicable — node counts, instance types, storage.}

| Cluster | Nodes | Instance Type | Storage |
|---------|-------|---------------|---------|
| {cluster-name} | {count} | {type} | {size} |

### Monitoring

Grafana dashboard:

- **Dashboard:** [{Dashboard Name}]({dashboard-url})
- **Key metrics:** {Metrics to watch}
- **Alerts:** {Critical alert conditions}

Available for regions: {list regions}

{If monitoring info is pending:}

## Components

{If this is a composite system with multiple sub-components.}

### {Component Category 1}

| Component | Type | Description |
|-----------|------|-------------|
| [[{component-link}\|{Component Name}]] | {type} | {description} |

### {Component Category 2}

| Component | Purpose |
|-----------|---------|
| [[{component-link}\|{Component Name}]] | {purpose} |

## Dependencies

| Component | Purpose | Dependency |
|-----------|---------|------------|
| [[{dependency-link}\|{Dependency Name}]] | {purpose} | **Hard** |
| [[{dependency-link}\|{Dependency Name}]] | {purpose} | Soft |

{Dependency types:}
- **Hard** — Component cannot function without this
- **Soft** — Component degrades gracefully without this

## Related

- [[Vault/{vault}/wiki/resources/components/{component}\|{Component Name}]] — Main component page (capabilities, integration)
- [[{related-infra-page}\|{Related Name}]] — {context}
- [[{source-link}\|{Source Name}]] — Deployment topology source

## Roadmap

{Only include if there's active development or migration timeline.}

### Timeline

| Phase | Timeline | Milestone |
|-------|----------|-----------|
| {phase} | {Q# YYYY} | {milestone} |

### Migration

{If migrating from legacy system.}

| Aspect | Legacy | New |
|--------|--------|-----|
| {aspect} | {old} | {new} |
```

---

## Minimal Infrastructure Component Page

For simpler components or initial documentation:

```markdown
---
Category: wiki
Tags: [component, infrastructure, {pillar}]
Source links:
- [[{source-link}]]
Created: {YYYY-MM-DD}
Last Updated: {YYYY-MM-DD}
---

# Infra {Component Name}

> **Note:** For component capabilities, see [[Vault/{vault}/wiki/resources/components/{component}|{Component Name}]] in the {vault} vault. This page documents deployment only.

{One-line description.}

## Deployment

### Environments & URIs

| Environment | Regions | URI Pattern |
|-------------|---------|-------------|
| dev | {region} | `{uri}` |
| staging | {regions} | `{uri}` |
| prod | {regions} | `{uri}` |

### Monitoring

Grafana dashboard: [{Dashboard Name}]({url})

## Related

- [[Vault/{vault}/wiki/resources/components/{component}\|{Component Name}]] — Main component page
- [[{source-link}\|{Source Name}]] — Deployment topology source
```

---

## Checklist

When creating an infra component page:

- [ ] Use `infra-{product}-{component}` naming convention
- [ ] Add cross-vault link to main component page (if exists)
- [ ] Include environments table (dev, staging, demo, prod)
- [ ] List all regions where deployed
- [ ] Add monitoring dashboard links
- [ ] Document dependencies with Hard/Soft classification
- [ ] Add Roadmap section only if timeline exists
- [ ] Update `wiki/portal.md` under Components
- [ ] Log the creation in `wiki/log.md`
