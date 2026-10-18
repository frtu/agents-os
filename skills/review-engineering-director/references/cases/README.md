# Worked Case Studies — index

The reference library behind `SKILL.md`: **cases** (recurring shapes), **theme guides** (playbooks by topic) and **templates** (artifacts to produce). It is generic on purpose: pattern-match the shape, not the specifics.

**Loading rule:** read this README first, then load **only** the files that match the doc or situation. That usually means one case and at most one guide, plus one template in Produce mode. Never read the whole library up front OR delegate selection to sub agents.

## Where the library comes from

- **Cases A–D** come from coaching on executive proposals and senior promotion packets. They are *doc-level* failures: what a weak claim looks like on the page.

## Cases

### Doc-level shapes (Review / Adversarial modes)

| Case | Shape to match | File |
| ---- | -------------- | ---- |
| A | Product-definition / vision doc: expansive capability catalog, no wedge, no explicit ask | `a-product-definition.md` |
| B | Commodity-looking work (migration, upgrade, refactor) claimed by category or output count | `b-commodity-migration.md` |
| C | A flat list of equal-weight bullets with no thesis | `c-bullet-point-pile.md` |
| D | Raw volume (MR count, tickets, hours) offered as proof of seniority | `d-effort-vs-seniority.md` |

## Heuristic quick map

Numbers refer to the table in `SKILL.md`. Heuristics 1–14 are doc judgement. 

## Growing the library

When you hit a **new recurring shape** that no case above captures, add it here so future runs reuse it, **without touching SKILL.md**:

1. Confirm it is genuinely new (not a variant of an existing case) and worth reusing. A variant goes into the existing case's *What surfaces* or the relevant guide instead.
2. Write `{next-letter}-{short-name}.md` in this folder. Use the frontmatter and body structure above, including *Common approach* and *Why this one diverges* for situation cases.
