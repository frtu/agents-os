# Template — component diagram

**Use for:** the one document the skill writes, `{repo}/docs/architecture/component-diagram.md`. Agent-filled.
**Pairs with:** the scan report from `scripts/scan_repo.py` (evidence), [`../classification.md`](../classification.md) (how to bucket and infer), and `diagram-architecture/references/mermaid-patterns.md` (Mermaid syntax).

Edit this file to change the output: headings, section order, table columns, diagram conventions. `scripts/check_diagram.py` reads the `##` headings of the skeleton below and requires each of them in the generated doc, so a heading you add, rename or remove here changes the gate too, with no code change.

## Skeleton

````markdown
# [Service name] — component diagram

> Reverse-engineered from the code at [commit short SHA or "working tree"] on [YYYY-MM-DD]. Evidence paths are relative to the repo root. ⚠ marks components inferred without code.

## Summary

[One paragraph, plain language: what the service is for, who calls it, what it depends on, how it runs.]

## Component diagram

```mermaid
flowchart TB
    subgraph UP["Upstream — callers & data sources"]
        [caller nodes]
    end
    subgraph SVC["[Service name]"]
        [API layer / core / embedded processes]
    end
    subgraph DOWN["Downstream — peers, cloud services, middleware"]
        [peer, cloud and store nodes]
    end
    subgraph XC["Cross-cutting — auth, observability, CI/CD"]
        [cross-cutting nodes]
    end
    [edges, each labelled with what flows or which API]

    classDef service fill:#dbeafe,stroke:#1d4ed8
    classDef upstream fill:#dcfce7,stroke:#15803d
    classDef downstream fill:#fef9c3,stroke:#a16207
    classDef crosscut fill:#f3e8ff,stroke:#7e22ce
    classDef inferred fill:#fee2e2,stroke:#b91c1c,stroke-dasharray:5 5
    class [service node ids] service
    class [upstream node ids] upstream
    class [downstream node ids] downstream
    class [cross-cutting node ids] crosscut
    class [inferred node ids] inferred
```

## Flows in a nutshell

1. [Trigger → service → effect, one line per flow]

## Components and evidence

| Component | Layer | Kind | What flows | Auth | Evidence |
| --- | --- | --- | --- | --- | --- |
| [name] | [upstream / downstream / middleware / cross-cutting] | [peer service / cloud service / database / cache / queue / storage / search / CI-CD / …] | [data, API path, topic] | [mechanism or "none found"] | `[path]`, `[path:line]` |

## Runtime specs

| Spec | Value | Evidence |
| --- | --- | --- |
| [Language + version] | [value] | `[path]` |

## Components not defined in this repo

| Component | Clue | Evidence | Confidence |
| --- | --- | --- | --- |
| ⚠ [name or "unknown [kind]"] | [what in the repo points to it] | `[path]` | [high / medium / low] |
````

## Section guidance

### Header line

- **Insight:** the reader knows how fresh the picture is and how to read ⚠.
- **Style:** one quoted line. Commit SHA when the repo is a git repo, else "working tree".

### Summary

- **Insight:** in 20 seconds, a newcomer knows what the service is for and where it sits.
- **Style:** one paragraph, 3–5 sentences, no jargon the diagram doesn't explain.
- **Questions to answer:** What business job does it do? Who calls it (or what triggers it)? What does it depend on to do that job? Where and how does it run?

### Component diagram

- **Insight:** every external touchpoint, its direction, and what crosses it, in one picture.
- **Style & format:**
  - `flowchart TB`, one subgraph per layer: upstream → the service (API layer / core / embedded processes) → downstream (workloads, stores, queues, peers, cloud services) + cross-cutting (auth issuer, observability, CI/CD, secrets). Drop an empty layer rather than leave an empty subgraph.
  - Edges: `-->` solid for data/control flow, `-.->` dashed for deploy/tooling links. Label every edge with what flows or the API path used.
  - Shapes: `[(...)]` datastores, `{{...}}` queues/topics, `([...])` entry points, `[...]` services.
  - Classes: `service`, `upstream`, `downstream`, `crosscut`, `inferred` (red, dashed border). Mark inferred components **in the diagram**, not only in the table, and prefix their label with ⚠.
  - Wrap any label containing `(`, `)`, `[`, `]`, `{` or `}` in double quotes. Node ids are unique and stable (`orders_db`, not `A1`).
  - Syntax help: `diagram-architecture/references/mermaid-patterns.md`.
- **Questions to answer:** Which way does each dependency point? Which edges carry auth? Which boxes are guesses?

### Flows in a nutshell

- **Insight:** the 3–6 paths that explain why the components exist.
- **Style:** numbered, at most 6, one line each: trigger → steps → effect. Name the nodes as they appear in the diagram.
- **Questions to answer:** What happens on the main request? What runs in the background (consumers, schedules)? What happens at deploy time?

### Components and evidence

- **Insight:** every box in the diagram is backed by a file, so a reader can check it.
- **Style:** one row per component drawn, in diagram order. Evidence is one or more backticked repo-relative paths (`path` or `path:line`). No row without evidence; inferred components go in the last section instead.
- **Questions to answer:** Where is the client, config block or SDK that proves this dependency? Which auth mechanism protects the call?

### Runtime specs

- **Insight:** what it takes to build and run the service.
- **Style:** table. Include: language + version, framework + version, container base image, what the image adds beyond the jar/binary (CLIs, binaries, sidecar configs), notable library pins (drivers, SDKs, auth libs), schema migrations owned here, observability endpoints. Pin versions when the manifest does; write "not pinned" otherwise.
- **Questions to answer:** Could someone rebuild the runtime from this table? What would a version upgrade touch?

### Components not defined in this repo

- **Insight:** honest gaps. "Something exists here, we don't know what" is a valid, valuable row.
- **Style:** one row per inferred component, ⚠ prefix, confidence `high` / `medium` / `low` (definitions in [`../classification.md`](../classification.md)). Write "None found" when the scan and review turned up nothing.
- **Questions to answer:** What is the clue? Which file shows it? What would confirm it (a repo to check, an owner to ask)?

## One-minute self-review

- [ ] Every component in the diagram has a row in *Components and evidence* or *Components not defined in this repo*.
- [ ] Every ⚠ row is styled `inferred` in the diagram.
- [ ] No secret values anywhere: names of keys and mechanisms only.
- [ ] Tables and short lines only; prose only in *Summary*.
