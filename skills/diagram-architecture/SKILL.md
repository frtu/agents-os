---
name: diagram-architecture
description: Generate architecture or integration diagrams using Mermaid syntax. Use when the user says "draw architecture", "create diagram", "mermaid diagram", "integration diagram", "flow diagram", or needs to visualize system components, data flows, or service interactions.
version: 0.1.0
---

# Diagram Architecture

Generate architecture and integration diagrams using Mermaid syntax for wiki pages and documentation.

## When to Use

- Creating architecture diagrams for wiki component pages
- Visualizing integration flows between systems
- Documenting data pipelines and service interactions
- Converting ASCII art diagrams to Mermaid format

## Diagram Types

| Type | Mermaid Syntax | Best For |
| --- | --- | --- |
| Flowchart | `flowchart TD` | Integration flows, data pipelines, request paths |
| Sequence | `sequenceDiagram` | API interactions, multi-service calls, auth flows |
| C4 Context | `C4Context` | High-level system boundaries |
| Block | `block-beta` | Layered architectures, stacks |

## Diagram Conversion & Alignment

When converting ASCII art diagrams to Mermaid, the tool automatically detects and preserves alignment:

### Alignment Detection

- **Vertical alignment (TD)**: Diagrams with `↓` arrows are converted to `flowchart TD`
- **Horizontal alignment (LR)**: Diagrams with `→` arrows are converted to `flowchart LR`

### Skipped Diagrams

The converter skips blocks containing box-drawing characters (`┌`, `┐`, `┘`, `┬`, `┴`, `┼`, `┤`, `├`) as these are typically UI mockups or ASCII art that don't convert well to Mermaid.

### Automatic Conversion

Use the `convert_ascii_to_mermaid.py` script:

```bash
# Convert single file (preserves alignment automatically)
python3 scripts/convert_ascii_to_mermaid.py /path/to/file.md

# Preview changes with --dry-run
python3 scripts/convert_ascii_to_mermaid.py --dry-run /path/to/file.md
```

## Instructions

1. **Identify the diagram type** based on what's being visualized:
   - **Top-down flows** (request → processing → response) → `flowchart TD`
   - **Time-ordered interactions** (service A calls B, B responds) → `sequenceDiagram`
   - **Layered stacks** (layers building on each other) → `flowchart TD` with subgraphs

2. **Use subgraphs** to group related components:
   ```mermaid
   flowchart TD
       subgraph Layer["Layer Name"]
           A[Component A]
           B[Component B]
       end
   ```

3. **Style conventions**:
   - Use `[Component]` for processes/services
   - Use `[(Database)]` for data stores
   - Use `{{Decision}}` for decision points
   - Use `([Start/End])` for entry/exit points

4. **Label edges** with the action or data flowing:
   ```mermaid
   A -->|"request"| B
   B -->|"response"| A
   ```

5. **Output format**: Always wrap in triple backticks with `mermaid` language tag.

## Example: Integration Flow

Convert this style of architecture description into Mermaid:

**Input context**: "Consumer sends request → Query Layer parses → Security Context built → Multi-Recall fans out to ES/ClickHouse/other stores → Fusion & Re-rank → Post-process → Return results"

**Output**:

```mermaid
flowchart TD
    subgraph Entry["Request Entry"]
        REQ([Consumer Request])
    end

    subgraph QueryLayer["Query Layer"]
        PARSE[Parse]
        OPT[Optimize/Compile]
        TRANS[Per-Backend Translate]
        PARSE --> OPT --> TRANS
    end

    subgraph Security["Security Context"]
        AUTH[AuthN - JWT/Passport]
        CTX[Build Context]
        AUTH --> CTX
    end

    subgraph MultiRecall["Multi-Recall"]
        ORCH[Orchestration]
        ES[(ES Index)]
        CH[(ClickHouse)]
        OTHER[(Other Store)]
        ORCH --> ES & CH & OTHER
    end

    subgraph Processing["Result Processing"]
        FUSION[Fusion & Re-Rank]
        POST[Post-Process]
        FUSION --> POST
    end

    subgraph Output["Response"]
        RESP([Unified Results])
    end

    REQ --> PARSE
    CTX --> ORCH
    TRANS --> CTX
    ES & CH & OTHER -->|filtered results| FUSION
    POST --> RESP

    style REQ fill:#e1f5fe
    style RESP fill:#c8e6c9
```

## Workflow

1. Read the source content (wiki page, notes, or user description)
2. Identify key components, their relationships, and data flows
3. Choose appropriate diagram type
4. Generate Mermaid code with proper structure
5. Insert into the wiki page under an `## Integration` or `## Architecture` section

## References

See `references/mermaid-patterns.md` for common diagram patterns.
