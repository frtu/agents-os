# Template: Wiki Updates and Report

Snippets for SKILL.md steps 8–11. Target files are listed in [vault-map](../vault-map.md) → Outputs.

## Product page — Candidate Pipeline

Add the table if it's missing, otherwise add or update the candidate's row:

```markdown
## Candidate Pipeline

| Candidate | Role | Status | Score |
|-----------|------|--------|-------|
| [[1-candidate-{slug}\|{Full Name}]] | {Title} ({Target}) | **Pre-Interview** | — |
```

## Portal — Candidate Evaluations

Under `#### Candidate Evaluations` → `##### product-{product}`:

```markdown
- [[1-candidate-{slug}|{Full Name}]] — {Target} candidate, {Brief background} — **Pre-Interview**
  - [[2-{step}-questions-{slug}|{Step} Guide]] — Tailored questions
```

## Log entry

Append to the log:

```markdown
## [{date}] ingest | Candidate {Name} (pre-interview)

Processed candidate materials for {Name} ({Role}, {Target}; floor {Floor}, stretch {Stretch}).

**Phase:** pre-interview
**Step:** {Step}
**Product:** {Product}

**Created:**
- [[1-candidate-{slug}|Candidate Evaluation]]
- [[2-{step}-questions-{slug}|{Step} Interview Guide]]
- [[source-{slug}|Source Profile]]

**Updated:**
- product-{product}.md — Candidate Pipeline table
- portal.md — Candidate Evaluations section
```

## Report to the user

```
Created: {candidate folder}/
├── 1-candidate-{slug}.md
└── 2-{step}-questions-{slug}.md

Source: wiki/sources/source-{slug}.md

Candidate: {Full Name}
Role: {Title} ({Target})
Product: {Product}
Interview Step: {Step}{ — step file applied: references/steps/{step}.md, if any}

Leveling: floor {Floor} / target {Target} / stretch {Stretch}
Central probe: {one line}
Assessment: {Strong count} Strong, {Probe count} Probe, {Gap count} Gap

Questions: {N} tailored questions across {M} categories

Ready for {Step} interview.
```
