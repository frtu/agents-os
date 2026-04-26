# Wiki Architecture

This document explains how the different categories of the wiki articulate with each other and guides AI in knowledge categorization.

## Overview

The real estate wiki is organized into 5 main categories that form a coherent system:

1. **Concepts** → Theoretical knowledge and conceptual tools of the domain
2. **Product** → What we want to do/achieve
3. **People** → Who does it and how to do it
4. **Resources** → What is produced and used
5. **Projects** → Concrete time-bounded initiatives

## 1. Concepts: Domain Foundations

Concepts constitute the theoretical base and domain knowledge for real estate.

### 1.1 Patterns (`concepts/patterns/`)

**Reusable investment models or strategies**

Examples:
- `gross-yield` / `net-yield`
- `property-tax-deficit`
- `furnished-rental-scheme` / `professional-rental-scheme`
- `tax-incentive-program`
- `bare-ownership`
- `real-estate-company` / `joint-ownership`

**Role**: Define different fiscal and financial approaches to real estate investment. These patterns are abstract and reusable.

### 1.2 Technologies (`concepts/technologies/`)

**Conceptual tools or capabilities for extracting data**

Examples:
- `land-registry`
- `mortgage-simulation`
- `wealth-management`

**Role**: Describe functional capabilities needed (calculators, simulators, etc.) without reference to specific implementation.

**Difference with Resources/Tools**: Technologies are generic concepts, while tools are concrete implementations (e.g., "land-registry" is a technology, "cadastre.gouv.fr" is a tool).

## 2. Product: What We Want to Achieve

The product category defines objectives, capabilities, and system users.

### 2.1 Entities (`product/entities/`)

**Business entities, resources, models, or logical product concepts**

Examples:
- `property`
- `tenant`
- `lease`
- `rent`
- `mortgage`
- `yield`
- `condo-fees`
- `tax`

**Role**: Model the business objects at the heart of the system. These entities are manipulated by features and fed by processes.

**Articulation**:
- Feed **features** (e.g., the `yield` entity is calculated by the `yield-calculation` feature)
- Are created/modified by **processes** (e.g., `lease` is created by the `lease-signing` process)
- Generate **artifacts** (e.g., `mortgage` generates an `amortization-schedule`)

### 2.2 Features (`product/features/`)

**Functional capabilities we want to achieve**

Examples:
- `yield-calculation`
- `mortgage-simulation`
- `market-analysis`
- `rental-management`

**Role**: Define functionalities offered to users.

**Articulation**:
- Manipulate **entities** (e.g., `yield-calculation` uses `property`, `rent`, `condo-fees`)
- Implement **patterns** (e.g., `tax-simulation` applies rules from `furnished-rental-scheme` or `property-tax-deficit`)
- Use conceptual **technologies**
- Are realized via **components** (e.g., `yield-calculator`)
- Are used by **personas**

### 2.3 Persona (`product/persona/`)

**User categories with similar profiles and skills**

Examples:
- `student-tenant`
- `young-couple-tenant`
- `landlord`
- `real-estate-agent`
- `beginner-investor`
- `experienced-investor`

**Role**: Identify who uses features and participates in processes.

**Articulation**:
- Use **features** (e.g., `beginner-investor` uses `mortgage-simulation`)
- Participate in **processes** (e.g., `landlord` conducts the `tenant-search` process)
- Are embodied by concrete **members** (e.g., fred is a `beginner-investor`)

## 3. People: Who and How to Achieve It

The people category defines actors, competencies, and methods to conduct operations.

### 3.1 Processes (`people/processes/`)

**Operational processes to conduct operations**

Examples:
- `property-search`
- `property-acquisition`
- `tenant-search`
- `rental-management`

**Role**: Describe workflows to follow to achieve an objective.

**Articulation**:
- Manipulate **entities** (e.g., `property-acquisition` creates a `property`, a `mortgage`)
- Use **features** (e.g., `property-search` uses `market-analysis`)
- Are decomposed into **steps** (e.g., `property-acquisition` contains `property-viewing`, `offer-signing`)
- Require **competencies** (e.g., `negotiation`, `financial-analysis`)
- Involve **members** (e.g., `notary-dupont`, `real-estate-agent-laforet`)
- Generate **artifacts** (e.g., `property-acquisition` produces `financing-plan`)

### 3.2 Members (`people/members/`)

**Specific individuals (names) from a team or network**

Examples:
- `fred`
- `property-hunter-francois`
- `real-estate-agent-laforet`
- `notary-dupont`

**Role**: Identify concrete actors who participate in processes.

**Articulation**:
- Embody **personas** (e.g., fred → `beginner-investor`)
- Execute **processes** (e.g., `notary-dupont` conducts `deed-signing`)
- Possess **competencies** (e.g., fred → `financial-analysis`)
- Perform **steps** (e.g., `property-hunter-francois` → `property-viewing`)
- Are external **dependencies** (e.g., `notary-dupont` → legal dependency)

### 3.3 Competencies (`people/competencies/`)

**Skills necessary for actors**

Examples:
- `financial-analysis`
- `negotiation`
- `rental-management`
- `real-estate-taxation`

**Role**: Define required know-how.

**Articulation**:
- Necessary for **processes** (e.g., `property-acquisition` requires `negotiation`, `financial-analysis`)
- Possessed by **members** (e.g., fred → `financial-analysis`)
- Used in **steps** (e.g., `offer-signing` requires `negotiation`)
- Build on **patterns** (e.g., `real-estate-taxation` uses `furnished-rental-scheme`, `property-tax-deficit`)

### 3.4 Steps (`people/steps/`)

**Detailed incremental steps with actors and competencies**

Examples:
- `property-viewing`
- `offer-signing`
- `deed-signing`
- `rental-listing`

**Role**: Decompose processes into granular actions.

**Articulation**:
- Compose **processes** (e.g., `property-acquisition` = `property-viewing` + `offer-signing` + `deed-signing`)
- Require **competencies** (e.g., `offer-signing` → `negotiation`)
- Involve **members** (e.g., `deed-signing` → `notary-dupont`)
- Produce **artifacts** (e.g., `offer-signing` → `purchase-offer`)
- Use **tools** (e.g., `property-viewing` → `property-valuation-tool` for evaluation)

## 4. Resources: What Is Produced and Used

The resources category gathers concrete outputs and dependencies.

### 4.1 Artifacts (`resources/artifacts/`)

**Items produced by the system or more physical concepts**

Examples:
- `amortization-schedule`
- `financing-plan`
- `yield-simulation`
- `purchase-offer`
- `authentic-deed`

**Role**: Concrete documents or deliverables generated.

**Articulation**:
- Produced by **processes** (e.g., `property-acquisition` → `financing-plan`)
- Produced by **steps** (e.g., `offer-signing` → `purchase-offer`)
- Generated by **components** (e.g., `yield-calculator` → `yield-simulation`)
- Materialize **entities** (e.g., `mortgage` → `amortization-schedule`)

### 4.2 Components (`resources/components/`)

**Modules of the developed system that bring value**

Examples:
- `yield-calculator`
- `tax-simulator`
- `dashboard`

**Role**: Functional parts of the built system.

**Articulation**:
- Implement **features** (e.g., `yield-calculator` → feature `yield-calculation`)
- Use **entities** (e.g., `yield-calculator` → `property`, `rent`)
- Apply **patterns** (e.g., `tax-simulator` → `furnished-rental-scheme`, `property-tax-deficit`)
- Generate **artifacts** (e.g., `tax-simulator` → `tax-simulation`)
- Consume **dependencies** (e.g., `yield-calculator` → data from `bank`)

### 4.3 Dependencies (`resources/dependencies/`)

**External dependencies on which management depends**

Examples:
- `bank`
- `notary`
- `real-estate-agency`
- `insurance`
- `property-manager`

**Role**: Essential external services or organizations.

**Articulation**:
- Provide data to **components** (e.g., `bank` → interest rates for `mortgage-simulator`)
- Intervene in **processes** (e.g., `notary` → `property-acquisition`)
- Are embodied by **members** (e.g., `notary-dupont` is an instance of the `notary` dependency)
- Provide **tools** (e.g., the `bank` dependency may offer an `online-mortgage-simulator` tool)

### 4.4 Tools (`resources/tools/`)

**Systems or tools directly usable (by human or AI)**

Examples:
- `seloger`
- `leboncoin`
- `pap`
- `rental-tension-meter`
- `property-valuation-tool`
- `yield-calculator-online`

**Role**: Concrete implementations of technologies (websites, APIs).

**Articulation**:
- Implement **technologies** (e.g., `cadastre.gouv.fr` → `land-registry` technology)
- Used in **processes** and **steps** (e.g., `property-search` uses `seloger`, `leboncoin`)
- Provided by **dependencies** (e.g., `bnp-mortgage-simulator` provided by `bank` dependency)
- Feed **components** with data (e.g., `property-valuation-tool` → `yield-calculator`)

## 5. Projects: Concrete Time-Bounded Initiatives

The projects category gathers concrete and temporal work.

### Hierarchical Structure

1. **Transversal initiatives**: `projects/{initiative-name}/`
   - Examples: `tax-optimization`, `refinancing`
   - **Role**: Transversal projects touching multiple properties or aspects

2. **Project groups**: `projects/{city-name}/`
   - Examples: `le-mans`, `angers`, `laval`
   - **Role**: Geographic grouping of rental projects

3. **Specific projects**: `projects/{city-name}/{project-name}/`
   - Examples: `10-rue-nationale-2-t3`, `5-avenue-republique-1-studio`
   - **Role**: Individual project with address and number of units

### Global Articulation of Projects

Projects are the **convergence point** of all other categories:

- Apply **patterns** (e.g., furnished-rental project, property-tax-deficit project)
- Use **technologies** and **tools** (e.g., `seloger` for search)
- Manipulate **entities** (e.g., creation of a `property`, signing of a `lease`)
- Target **features** (e.g., achieve a target yield)
- Target **personas** (e.g., `student-tenant`)
- Follow **processes** (e.g., `property-acquisition`, `tenant-search`)
- Involve **members** (e.g., `fred`, `notary-dupont`)
- Require **competencies** (e.g., `negotiation`, `financial-analysis`)
- Decomposed into **steps** (e.g., `property-viewing`, `offer-signing`)
- Generate **artifacts** (e.g., `financing-plan`, `lease`)
- Use **components** (e.g., `yield-calculator`)
- Depend on **dependencies** (e.g., `bank`, `notary`)

**Concrete example**: Project `le-mans/10-rue-nationale-2-t3`
- Pattern: `furnished-rental-scheme`
- Process: `property-acquisition` → `rental-listing`
- Members: `fred`, `notary-dupont`, `real-estate-agent-laforet`
- Competencies: `financial-analysis`, `negotiation`
- Steps: `property-viewing` → `offer-signing` → `deed-signing` → `rental-listing`
- Entities: `property`, `mortgage`, `lease`, `tenant`
- Artifacts: `financing-plan`, `amortization-schedule`, `lease`
- Tools: `seloger`, `property-valuation-tool`, `mortgage-simulator`
- Dependencies: `bank`, `notary`, `real-estate-agency`

## AI Categorization Guide

### How to decide in which category to place information?

#### Decision Flowchart

1. **Is it theoretical/reusable domain knowledge?** → `concepts/`
   - Investment strategy? → `concepts/patterns/`
   - Conceptual capability (calculator, simulator)? → `concepts/technologies/`

2. **Is it a definition of what we want to do?** → `product/`
   - Business object / data model? → `product/entities/`
   - Functional capability? → `product/features/`
   - User type? → `product/persona/`

3. **Is it related to who does it or how to do it?** → `people/`
   - Workflow / methodology? → `people/processes/`
   - Named person? → `people/members/`
   - Know-how / skill? → `people/competencies/`
   - Granular action in a workflow? → `people/steps/`

4. **Is it something produced or used?** → `resources/`
   - Generated document / deliverable? → `resources/artifacts/`
   - Developed system module? → `resources/components/`
   - External service / organization? → `resources/dependencies/`
   - Concrete tool (site/API)? → `resources/tools/`

5. **Is it concrete time-bounded work?** → `projects/`
   - Transversal initiative? → `projects/{initiative-name}/`
   - Real estate project in a city? → `projects/{city-name}/{project-name}/`

### Categorization Examples

| Content | Category | Justification |
|---------|----------|---------------|
| Furnished rental scheme | `concepts/patterns/` | Reusable tax strategy |
| Land registry | `concepts/technologies/` | Conceptual capability to obtain land data |
| Cadastre.gouv.fr | `resources/tools/` | Concrete implementation of land-registry technology |
| Lease | `product/entities/` | Core business object |
| Yield calculation | `product/features/` | Functional capability offered |
| Beginner investor | `product/persona/` | User type |
| Property acquisition | `people/processes/` | Complete workflow |
| Fred | `people/members/` | Named person |
| Negotiation | `people/competencies/` | Required skill |
| Offer signing | `people/steps/` | Step in a process |
| Financing plan | `resources/artifacts/` | Produced document |
| Yield calculator | `resources/components/` | System module |
| Bank | `resources/dependencies/` | External dependency |
| SeLoger | `resources/tools/` | Usable tool |
| 10 rue Nationale 2 T3 | `projects/le-mans/` | Concrete localized project |

### Ambiguous Cases and Resolution

#### "Notary Dupont"
- **Ambiguity**: Person (`people/members/`) or dependency (`resources/dependencies/`)?
- **Resolution**:
  - `notary-dupont` → `people/members/` (named person)
  - `notary` → `resources/dependencies/` (dependency category)

#### "Yield simulation"
- **Ambiguity**: Feature, artifact, or component?
- **Resolution**:
  - `yield-simulation` → `resources/artifacts/` (produced document)
  - `yield-calculation` → `product/features/` (functional capability)
  - `yield-calculator` → `resources/components/` (module implementing the feature)

#### "SeLoger"
- **Ambiguity**: Technology or tool?
- **Resolution**:
  - `listing-search` → `concepts/technologies/` (conceptual capability)
  - `seloger` → `resources/tools/` (concrete implementation)

## Consistency Principles

### 1. Conceptual → Concrete Hierarchy

```
concepts/technologies/      (abstract)
    ↓
product/features/           (objective)
    ↓
resources/components/       (implementation)
    ↓
resources/tools/            (external concrete)
```

### 2. Role → Person Hierarchy

```
product/persona/            (user type)
    ↓
people/members/             (named person)
```

### 3. Process → Action Hierarchy

```
people/processes/           (complete workflow)
    ↓
people/steps/               (granular action)
```

### 4. Capability → Deliverable Hierarchy

```
product/features/           (capability)
    ↓
resources/artifacts/        (deliverable)
```

## Conclusion

This categorization system creates a coherent semantic network where:

- **Concepts** provide theoretical knowledge
- **Product** defines objectives
- **People** organize execution
- **Resources** materialize results
- **Projects** integrate everything into concrete initiatives

The AI must always seek the **appropriate level of specificity** and use **articulations between categories** to correctly place each piece of knowledge in the wiki.
