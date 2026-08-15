# Wiki Architecture

This document explains how the different categories of the wiki articulate with each other and guides AI in knowledge categorization.

## Overview

The wiki is organized into 6 main categories that form a coherent system:

1. **Concepts** → Theoretical knowledge and reusable patterns
2. **Product** → What we build and deliver (organized by type: entities, features, personas)
3. **People** → Who builds it and how to build it
4. **Resources** → What is produced and depended upon
5. **Projects** → Time-bounded development initiatives
6. **Synthesis** → Cross-cutting analyses and comparisons

## Search Vault Specificity

The search vault organizes **Product** into flat capability categories:

- **Entities** (`product/entities/`) — Core product objects (metadata structures, data models, infrastructure configs)
- **Features** (`product/features/`) — Product capabilities (management, querying, protection)
- **Personas** (`product/persona/`) — Users of product capabilities

## 1. Concepts: Reusable Knowledge

Concepts constitute the foundational patterns and technologies applicable across the platform.

### 1.1 Patterns (`concepts/patterns/`)

**Development patterns and architectural principles**

Examples:
- `idempotency`
- `dead-letter-queue`
- `reliability`
- `security`
- `deployment`
- `canary`
- `self-healing`

**Role**: Define reusable software engineering patterns and best practices that guide system design and implementation.

**Articulation**:
- Applied in **processes** (e.g., `software-engineering` process uses `idempotency`, `reliability`)
- Implemented by **components** (e.g., `retry-handler` implements `idempotency`)
- Guide **features** design (e.g., `rate-limiting` feature applies `circuit-breaker` pattern)

### 1.2 Technologies (`concepts/technologies/`)

**Reusable technologies (protocols, infrastructure, messaging)**

Examples:
- `mcp`
- `database`
- `kafka`
- `rag`
- `elasticsearch`
- `flink`

**Role**: Describe technological capabilities and platforms that can be leveraged.

**Articulation**:
- Implemented by **dependencies** (e.g., `kafka` technology → `kafka-cluster` dependency)
- Used by **components** (e.g., `search-service` uses `elasticsearch` technology)
- Enable **features** (e.g., `real-time-indexing` feature uses `kafka` technology)
- Documented as **tools** when external (e.g., `elasticsearch-api` tool)

**Difference with Resources**:
- **Technologies** are conceptual capabilities (e.g., "distributed messaging")
- **Dependencies** are concrete systems we depend on (e.g., "Kafka cluster on k8s")
- **Tools** are usable interfaces (e.g., "Kafka CLI", "Elasticsearch API")

## 2. Product: What We Build

The product category is organized into three flat capability categories that encompass all product aspects.

### 2.1 Entities (`product/entities/`)

**Core product objects across all capability areas**

#### Scope:
- Index and alias lifecycle management objects
- Schema and mapping definitions
- Data models and query structures
- Infrastructure constraints and configurations

#### Examples:
- Metadata-related: `index`, `alias`, `mapping`, `index-template`
- Data-related: `search-template`, `query`, `aggregation`, `document`
- Infra-related: `quota`, `policy`, `rate-limit`, `circuit-breaker-config`

#### Role:
Define the structural elements, data models, and configuration objects of the platform.

#### Articulation:
- **Entities** are manipulated by **features** (e.g., `index-template` → `template-management`)
- **Entities** power **features** (e.g., `search-template` enables `universal-search`)
- **Entities** configure **features** (e.g., `rate-limit` entity → `rate-limiting` feature)
- **Components** manipulate entities (e.g., `template-service` creates `index-template` entities)
- **Artifacts** materialize entities (e.g., `index-configuration` artifact)

### 2.2 Features (`product/features/`)

**All product capabilities and operations**

#### Scope:
- Metadata/structure management (indexing, schema, template operations)
- Data manipulation (querying, analytics, search operations)
- Infrastructure/protection (rate limiting, authentication, resilience)

#### Examples:
- Management: `alias-management`, `template-management`, `index-creation`, `schema-validation`
- Data: `universal-search`, `analytics`, `federated-search`, `semantic-search`, `auto-complete`
- Protection: `rate-limiting`, `authentication`, `circuit-breaker`, `quota-management`

#### Role:
Define operations and capabilities that the platform delivers to users and systems.

#### Articulation:
- **Features** manipulate **entities** (e.g., `template-management` manipulates `index-template`)
- **Features** are used by **personas** (e.g., `domain-developer` uses `alias-management`)
- **Features** apply **patterns** (e.g., `universal-search` applies `routing`, `federation`)
- **Features** are implemented by **components** (e.g., `template-service` implements `template-management`)
- **Features** protect each other (e.g., `rate-limiting` protects `search-gateway`)

### 2.3 Personas (`product/persona/`)

**All users and teams interacting with product capabilities**

#### Scope:
- Platform configuration and management
- Data consumption and analysis
- Infrastructure collaboration and operations

#### Examples:
- Configuration: `domain-developer`, `platform-engineer`, `schema-designer`
- Data: `ops-team`, `data-analyst`, `application-developer`, `end-user`
- Infrastructure: `infra-t0-team`, `data-infra-team`, `security-team`, `platform-sre`

#### Role:
Identify all types of users and teams who interact with or manage product capabilities.

#### Articulation:
- **Personas** use **features** (e.g., `ops-team` uses `analytics`, `domain-developer` uses `index-creation`)
- **Personas** configure **entities** (e.g., `platform-sre` manages `quota` entities)
- **Personas** are embodied by **members** (e.g., `fred` → `domain-developer`, `platform-engineer`)
- **Personas** require **competencies** (e.g., `schema-designer` requires `elasticsearch-expertise`)
- **Personas** execute **processes** (e.g., `domain-developer` executes `software-engineering`)

## 3. People: Who Builds and How to Build

The people category defines actors, workflows, competencies, and granular actions.

### 3.1 Processes (`people/processes/`)

**Workflows and methodologies to achieve outcomes**

Examples:
- `software-engineering`
- `regulatory-audit`
- `incident-response`
- `capacity-planning`

**Role**: Define how work gets done across teams.

**Articulation**:
- Use **patterns** (e.g., `software-engineering` applies `canary`, `deployment` patterns)
- Manipulate **entities** across domains (e.g., `capacity-planning` adjusts `quota` entities)
- Deliver **features** (e.g., `software-engineering` builds new features)
- Decomposed into **steps** (e.g., `software-engineering` = `development` + `unit-testing` + `deployment`)
- Require **competencies** (e.g., `software-engineering` needs `system-design`)
- Involve **members** (e.g., `fred` conducts `software-engineering`)
- Produce **artifacts** (e.g., `software-engineering` produces `source-code`, `binary-package`)

### 3.2 Members (`people/members/`)

**Specific individuals from teams**

Examples:
- `fred`
- `platform-lead-john`
- `sre-alice`

**Role**: Identify concrete actors executing work.

**Articulation**:
- Embody **personas** (e.g., `fred` → `domain-developer`, `platform-engineer`)
- Execute **processes** (e.g., `fred` conducts `software-engineering`)
- Possess **competencies** (e.g., `fred` → `system-design`, `elasticsearch-expertise`)
- Perform **steps** (e.g., `fred` → `development`, `deployment`)
- Work on **projects** (e.g., `fred` works on `search-platform/universal-search`)

### 3.3 Competencies (`people/competencies/`)

**Hard and soft skills needed**

Examples:
- `system-design`
- `leadership`
- `elasticsearch-expertise`
- `kafka-administration`
- `security-architecture`

**Role**: Define required skills for processes and steps.

**Articulation**:
- Required by **processes** (e.g., `software-engineering` requires `system-design`)
- Required by **steps** (e.g., `deployment` requires `kubernetes-operations`)
- Possessed by **members** (e.g., `fred` has `system-design`)
- Build on **technologies** knowledge (e.g., `elasticsearch-expertise` requires understanding `elasticsearch` technology)
- Enable **features** development (e.g., `system-design` enables building `universal-search`)

### 3.4 Steps (`people/steps/`)

**Granular actions within workflows**

Examples:
- `development`
- `unit-testing`
- `deployment`
- `release-management`
- `code-review`

**Role**: Break down processes into executable actions.

**Articulation**:
- Compose **processes** (e.g., `software-engineering` = `development` + `unit-testing` + `deployment`)
- Require **competencies** (e.g., `deployment` requires `kubernetes-operations`)
- Performed by **members** (e.g., `fred` performs `development`)
- Apply **patterns** (e.g., `deployment` applies `canary` pattern)
- Produce **artifacts** (e.g., `development` produces `source-code`)
- Use **tools** (e.g., `code-review` uses `github`, `deployment` uses `argocd`)

## 4. Resources: What Is Produced and Depended Upon

The resources category encompasses outputs, system modules, dependencies, and tools.

### 4.1 Artifacts (`resources/artifacts/`)

**Tangible outputs produced by the system**

Examples:
- `source-code`
- `binary-package`
- `deployment-pipeline`
- `monitoring-dashboard`
- `api-documentation`

**Role**: Document concrete deliverables and outputs.

**Articulation**:
- Produced by **processes** (e.g., `software-engineering` → `source-code`, `binary-package`)
- Produced by **steps** (e.g., `development` → `source-code`, `deployment` → `deployment-pipeline`)
- Generated by **components** (e.g., `api-gateway` → `api-documentation`)
- Materialize **entities** (e.g., `index-template` → `template-configuration-file`)
- Consumed by other **processes** (e.g., `deployment-pipeline` consumed by `release-management`)

### 4.2 Components (`resources/components/`)

**System modules delivering value**

Examples:
- `search-gateway`
- `indexing-service`
- `template-service`
- `monitoring-service`
- `authentication-service`

**Role**: Functional building blocks of the search platform.

**Articulation**:
- Implement **features** across domains:
  - Metadata: `template-service` implements `template-management`
  - Data: `search-gateway` implements `universal-search`
  - Infra: `authentication-service` implements `authentication`
- Manipulate **entities** (e.g., `indexing-service` creates `document` entities)
- Apply **patterns** (e.g., `search-gateway` applies `circuit-breaker`, `retry` patterns)
- Use **technologies** (e.g., `search-gateway` uses `elasticsearch`, `kafka`)
- Depend on **dependencies** (e.g., `indexing-service` depends on `kafka-cluster`)
- Produce **artifacts** (e.g., `search-gateway` produces `api-documentation`)
- Built through **processes** (e.g., `software-engineering` builds components)

### 4.3 Dependencies (`resources/dependencies/`)

**External systems our platform depends on**

Examples:
- `kubernetes` resources: `pvc`, `pod`, `service`
- `kafka-cluster`
- `elasticsearch-cluster`
- `flink` resources: `checkpoint-storage`, `state-backend`
- `schema-registry`
- `service-discovery`

**Role**: Infrastructure and external systems required for operation.

**Articulation**:
- Implement **technologies** (e.g., `kafka-cluster` dependency → `kafka` technology)
- Provide services to **components** (e.g., `elasticsearch-cluster` → `search-gateway`)
- Configured via **infra features** (e.g., `quota-management` manages `pvc` quotas)
- Managed by **infra personas** (e.g., `data-infra-team` manages `kafka-cluster`)
- Monitored through **tools** (e.g., `kubernetes-dashboard` monitors `pod` health)
- Required by **projects** (e.g., `search-platform/universal-search` requires `elasticsearch-cluster`)

### 4.4 Tools (`resources/tools/`)

**Out-of-the-box systems usable by humans or AI**

Examples:
- `jira`
- `github`
- `argocd`
- `grafana`
- `elasticsearch-api`
- `kafka-cli`
- `google-docs`

**Role**: Ready-to-use tools and platforms.

**Articulation**:
- Implement **technologies** (e.g., `elasticsearch-api` tool → `elasticsearch` technology)
- Used in **steps** (e.g., `deployment` step uses `argocd` tool)
- Used in **processes** (e.g., `software-engineering` uses `github`, `jira`)
- Provided by **dependencies** (e.g., `elasticsearch-cluster` provides `elasticsearch-api`)
- Enable **features** usage (e.g., `grafana` visualizes data from `analytics` feature)
- Used by **personas** (e.g., `domain-developer` uses `jira`, `github`)

## 5. Projects: Time-Bounded Development Work

The projects category tracks concrete initiatives with defined scope and timeline.

### Hierarchical Structure

1. **Transversal initiatives**: `projects/{initiative-name}/`
   - Examples: `kafka-migration`, `sso-enforcement`, `elasticsearch-upgrade`
   - **Role**: Cross-cutting projects affecting multiple products/components

2. **Product/Platform**: `projects/{product-name}/`
   - Examples: `search-platform`, `analytics-platform`
   - **Role**: Broad product or platform grouping

3. **Specific projects**: `projects/{product-name}/{project-name}/`
   - Examples: `search-platform/universal-search`, `search-platform/semantic-search`
   - **Role**: Concrete feature or capability development

### Global Articulation of Projects

Projects integrate **all categories**:

- Apply **patterns** (e.g., `universal-search` project applies `federation`, `routing` patterns)
- Use **technologies** (e.g., `kafka-migration` migrates to `kafka` technology)
- Manipulate **entities** (e.g., configure indexes and schemas, build data models)
- Deliver **features** (e.g., `universal-search` project delivers the `universal-search` feature)
- Serve **personas** (e.g., `ops-team`, `domain-developer`)
- Follow **processes** (e.g., `software-engineering`, `regulatory-audit`)
- Involve **members** (e.g., `fred`, `platform-lead-john`)
- Require **competencies** (e.g., `system-design`, `elasticsearch-expertise`)
- Execute **steps** (e.g., `development`, `testing`, `deployment`)
- Produce **artifacts** (e.g., `source-code`, `deployment-pipeline`)
- Build **components** (e.g., `search-gateway`)
- Depend on **dependencies** (e.g., `elasticsearch-cluster`, `kafka-cluster`)
- Use **tools** (e.g., `github`, `jira`, `argocd`)

**Concrete example**: Project `search-platform/universal-search`
- **Patterns**: `federation`, `routing`, `circuit-breaker`
- **Technologies**: `elasticsearch`, `kafka`
- **Product capabilities**:
  - Define `search-template` entity, use `template-management` feature
  - Build `universal-search` feature, serve `ops-team` persona
  - Apply `rate-limiting`, `authentication` features
- **Process**: `software-engineering`
- **Members**: `fred`, `platform-engineer-alice`
- **Competencies**: `system-design`, `elasticsearch-expertise`
- **Steps**: `development` → `unit-testing` → `deployment` → `release-management`
- **Artifacts**: `source-code`, `api-documentation`, `deployment-pipeline`
- **Components**: `search-gateway`, `query-router`
- **Dependencies**: `elasticsearch-cluster`, `kubernetes`
- **Tools**: `github`, `jira`, `argocd`, `elasticsearch-api`

## 6. Synthesis: Cross-Cutting Analyses

**Purpose**: Comparisons, analyses, and cross-cutting themes that don't fit neatly into other categories.

Examples:
- Technology comparisons (e.g., "Elasticsearch vs Solr")
- Architecture decision records (ADRs)
- Performance benchmarks
- Security assessments
- Cost analyses

**Articulation**:
- References multiple **technologies**, **patterns**, **features**
- Informs **project** decisions
- Guides **architecture** choices
- Supports **competency** development

## AI Categorization Guide

### Decision Flowchart

1. **Is it reusable domain knowledge?** → `concepts/`
   - Development pattern or principle? → `concepts/patterns/`
   - Technology or protocol? → `concepts/technologies/`

2. **Is it a product capability or related object?** → `product/`
   - **What type of content?**
     - Core object/model? → `product/entities/`
     - Capability/operation? → `product/features/`
     - User/team type? → `product/persona/`

3. **Is it about who or how?** → `people/`
   - Workflow/methodology? → `people/processes/`
   - Named person? → `people/members/`
   - Skill/competency? → `people/competencies/`
   - Granular action? → `people/steps/`

4. **Is it produced or depended upon?** → `resources/`
   - Output/deliverable? → `resources/artifacts/`
   - System module we build? → `resources/components/`
   - External system we depend on? → `resources/dependencies/`
   - Ready-to-use tool? → `resources/tools/`

5. **Is it time-bounded work?** → `projects/`
   - Transversal initiative? → `projects/{initiative-name}/`
   - Product/platform work? → `projects/{product-name}/{project-name}/`

6. **Is it a comparison or analysis?** → `synthesis/`

### Categorization Examples

| Content | Category | Justification |
|---------|----------|---------------|
| Idempotency | `concepts/patterns/` | Reusable development pattern |
| Kafka | `concepts/technologies/` | Technology we can leverage |
| Index | `product/entities/` | Core product object |
| Alias management | `product/features/` | Product capability |
| Domain developer | `product/persona/` | User of product capabilities |
| Universal search | `product/features/` | Product capability |
| Ops team | `product/persona/` | User of product capabilities |
| Rate limiting | `product/features/` | Product protection capability |
| Platform SRE | `product/persona/` | Infrastructure manager |
| Software engineering | `people/processes/` | Development workflow |
| Fred | `people/members/` | Named team member |
| System design | `people/competencies/` | Required skill |
| Deployment | `people/steps/` | Granular process action |
| Source code | `resources/artifacts/` | Produced output |
| Search gateway | `resources/components/` | System module we build |
| Elasticsearch cluster | `resources/dependencies/` | External system dependency |
| JIRA | `resources/tools/` | Ready-to-use tool |
| Kafka migration | `projects/kafka-migration/` | Transversal initiative |
| Universal search project | `projects/search-platform/universal-search/` | Specific product project |
| Elasticsearch vs Solr | `synthesis/` | Technology comparison |

### Ambiguous Cases and Resolution

#### "Elasticsearch"
- **Ambiguity**: Technology, dependency, or tool?
- **Resolution**:
  - `elasticsearch` → `concepts/technologies/` (technology concept)
  - `elasticsearch-cluster` → `resources/dependencies/` (concrete system we depend on)
  - `elasticsearch-api` → `resources/tools/` (usable interface)

#### "Search"
- **Ambiguity**: Entity or feature?
- **Resolution**:
  - `search-template` → `product/entities/` (data model entity)
  - `universal-search` → `product/features/` (search capability feature)
  - `search-gateway` → `resources/components/` (component implementing features)

#### "Rate limit"
- **Ambiguity**: Entity, feature, or pattern?
- **Resolution**:
  - `rate-limit` (configuration object) → `product/entities/` (infrastructure config entity)
  - `rate-limiting` (capability) → `product/features/` (protection feature)
  - `throttling` (approach) → `concepts/patterns/` (pattern)

#### "Domain developer"
- **Ambiguity**: What persona and context?
- **Resolution**: Generic persona focused on platform configuration
  - `domain-developer` → `product/persona/` (platform configuration user)
  - May use features across all capability areas (metadata, data, infra)

## Consistency Principles

### 1. Flat Product Organization

```
product/entities/     — All product objects
    index, alias, mapping, template          (structure)
    search-template, query, aggregation      (data)
    quota, policy, rate-limit                (infrastructure)

product/features/     — All product capabilities
    index-creation, alias-management        (management)
    universal-search, analytics             (data)
    rate-limiting, authentication           (protection)

product/persona/      — All product users
    domain-developer, platform-engineer     (configuration)
    ops-team, data-analyst                  (data consumption)
    platform-sre, security-team             (infrastructure)
```

### 2. Technology Hierarchy

```
concepts/technologies/      (abstract capability)
    ↓
resources/dependencies/     (concrete system)
    ↓
resources/tools/            (usable interface)
```

Example: `kafka` (technology) → `kafka-cluster` (dependency) → `kafka-cli` (tool)

### 3. Feature Implementation Chain

```
product/{domain}/features/     (capability definition)
    ↓
resources/components/          (implementation)
    ↓
resources/artifacts/           (output)
```

Example: `universal-search` (feature) → `search-gateway` (component) → `api-documentation` (artifact)

### 4. Process Decomposition

```
people/processes/              (workflow)
    ↓
people/steps/                  (actions)
    ↓
resources/artifacts/           (outputs)
```

Example: `software-engineering` (process) → `development` + `deployment` (steps) → `source-code` + `deployment-pipeline` (artifacts)

## Conclusion

The search platform wiki creates a flat, capability-focused knowledge structure where:

- **Concepts** provide reusable patterns and technologies
- **Product** organizes capabilities into entities, features, and personas (flat structure)
- **People** define actors, workflows, skills, and actions
- **Resources** track outputs, components, dependencies, and tools
- **Projects** integrate everything into time-bounded work
- **Synthesis** captures cross-cutting analyses

The AI must:
1. **Categorize by content type** for product content (entity, feature, or persona)
2. **Distinguish abstraction levels** (concepts → dependencies → tools)
3. **Follow the hierarchies** (process → steps → artifacts; features → components)
4. **Use appropriate specificity** (transversal initiative vs specific project)

This flat product organization simplifies navigation while maintaining clear categorization rules across all capability areas.
