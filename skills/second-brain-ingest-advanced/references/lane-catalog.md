# Lane catalog

Standard lanes for each phase. Pick lanes so that, **within a phase, no two lanes share a folder**.
Folder names follow the second-brain wiki layout. Check the vault's `docs/wiki-architecture*.md`
for overrides.

## Partition rule

Split by **destination folder**, never by source. When one source feeds many folders, give it to several
lanes, each extracting only its own concern. When one folder would receive pages from many sources, give
all those sources to the one lane that owns the folder.

Size each lane at 5–20 pages. Above 20, split the folder by sub-theme with explicit file lists,
not overlapping folders.

## Phase 1 — atomic

| Lane              | write_scope (typical)                                         | Creates                            | Typical updates                                                         | Instruction core                                                                                       |
| ----------------- | ------------------------------------------------------------- | ---------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `members`         | `wiki/people/members/`                                        | one page per named person          | existing member pages *of others*                                       | Role, level link, achievements with numbers, challenges, competencies with anchors, related features   |
| `features-specs`  | `wiki/product/features/`, `wiki/product/specs/`               | one page per capability or spec    | —                                                                       | Problem before → what was built → quantified outcomes → business value → contributors → decision owner |
| `patterns`        | `wiki/concepts/patterns/`, `wiki/people/competencies/`        | one page per reusable approach     | existing patterns (add field notes), competency pages (add field notes) | Definition, why, how to apply, example with numbers, anti-pattern; merge rather than duplicate         |
| `sources-profile` | `wiki/sources/`, plus exact files for the subject's own pages | one `source-*` page per raw source | the subject's profile page(s)                                           | Factual source summaries; profile enrichment, each fact tagged by source                               |
| `processes-steps` | `wiki/people/processes/`, `wiki/people/steps/`                | one process plus N steps           | —                                                                       | Ordered stages, Input/Action/Output, prev/next chain                                                   |
| `components`      | `wiki/resources/components/`, `wiki/resources/artifacts/`     | systems and deliverables           | —                                                                       | PTCA cross-links; follow the component page structure                                                  |

Profile-type pages (for example the person a resume belongs to) go in **one** lane as exact files.
The `members` lane's folder scope must exclude them. If you can't express that, list the `members` lane's
files exactly instead of giving it the whole folder.

## Phase 2 — bubble up

| Lane             | write_scope                                                                                      | Creates                                                                    | Instruction core                                                                                                                                           |
| ---------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `product-rollup` | `wiki/product/entities/`, `wiki/synthesis/<exact files>`, `wiki/product/features/` (append-only) | an entity page, an outcomes synthesis, a vision/operating-system synthesis | BLUF headline numbers; weighted streams → features; member table; business-value lens; gaps                                                                |
| `evidence-map`   | `wiki/synthesis/<exact file>`, the subject's profile (append to Related)                         | a reference page mapping evidence to a framework (role levels, rubric)     | One table per framework dimension: expectation → evidence (linked, with number) → present in artifact? → strength; ranked hero facts; inconsistency ledger |

The two lanes above share `wiki/synthesis/`, so give each **exact files**, never the folder.

## Phase 3 — deliverable

| Lane | write_scope | Creates | Instruction core |
| --- | --- | --- | --- |
| `deliverable` | `output/<exact file>` | one external document | Apply the named lens skill. Kill / downgrade / fix / missing / rewrite / unresolved / verdict / references. The original is never modified. |

## Orchestrator-owned (never in a lane)

- `wiki/portal.md` and `wiki/log.md`
- Any page that two lanes would both need to edit. The orchestrator edits it after the gate.
