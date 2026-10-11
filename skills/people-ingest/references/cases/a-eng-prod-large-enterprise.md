---
case: A
name: Dual-track engineering ladder, 500+ engineers
shape: Large engineering org with a full leveling framework — dual track, per-track
  differentiation dimensions, per-skill depth tables, delivery processes with steps, and
  personas per delivery role.
source: management vault (IC and Management matrix, four dimensions per track)
---

# Case A — Dual-track engineering ladder, 500+ engineers

## Context

An engineering & product organization past 500 engineers has usually accumulated: a leveling matrix (likely revised more than once), legacy ladder documents per level, per-skill definitions,
delivery processes (SDLC, hiring, retrospectives), and role descriptions for the people involved
in delivery. The vault must hold all of these without letting them contradict each other, and
must survive a framework revision (re-clustering) without breaking links.

Sources arrive in clusters: the current matrix (source of truth), legacy per-level ladders
(extraction source, kept as history), skill definitions, process frameworks, and role/persona
descriptions that belong to delivery governance rather than the ladder.

## Information structure

```
wiki/people/
├── roles/
│   ├── {ladder-overview}.md            ONE page: "how does this org level people?"
│   │                                     both tracks, both dimension tables, legacy traceability
│   └── role-{track}-{level}.md         LEVEL pages, one per rung (incl. intermediate tiers):
│                                         altitude, craft time %, per-dimension expectations,
│                                         level differentiation (← prev / → next, key transitions)
├── competencies/
│   ├── {dimension}.md                  DIMENSION pages: the axes that *differentiate* levels
│   │                                     — what makes "more senior" mean more senior
│   ├── {skill}.md                      SKILL pages: depth progression per level per track,
│   │                                     measurement indicators, red flags, growth actions,
│   │                                     where the skill applies in process steps
│   └── {legacy-category}.md            LEGACY pages: pre-revision categories, each stating its
│                                         re-cluster destination — kept only for traceability
├── processes/{process}.md              repeatable workflows (SDLC, hiring loop, retrospective)
├── steps/step-{process}-{n}-{name}.md  granular steps: skills applied, inputs/outputs, gates
└── members/{name}.md                   persons, mapped to role + level + observed skills
```

Each layer answers one question:

| Layer | Question it answers |
|-------|--------------------|
| Ladder overview | How does the org level people? (tracks, levels, dimensions at a glance) |
| Role page | What is expected at this rung? (altitude, craft time, per-dimension expectations) |
| Dimension page | What differentiates levels? (definition, competencies, calibration signal) |
| Skill page | What does good look like per level? (depth tables, indicators, red flags, growth) |
| Process/step page | Where are skills exercised? (steps, skills applied, quality gates) |
| Persona page | What does this role *do* in delivery? (responsibilities, constraints, gates owned) |
| Member page | Who is this person, mapped to the frame? (role link, level, evidence) |
| Matrix artifact | The company's concrete calibration tool (implements the generic ladder concept) |

## Articulations

Every arrow is a wikilink, both directions:

- **Role ↔ Skill**: role pages hold 3-column expectation tables (Competency with track anchor
  Skill, Depth, Expectations); skill pages hold depth
  tables whose level cells link back to role pages. Depth lives on skill pages, expectations on
  role pages — never duplicated in both.
- **Skill ↔ Dimension**: skill pages name their primary dimension (plus legacy category for
  traceability); dimension pages list their skills. One competency has exactly **one primary
  home** — double counting breaks calibration.
- **Skill/Role ↔ Step**: skill pages carry an "SDLC Application" section linking the steps where
  the skill applies; step pages link the skills applied in them.
- **Persona ↔ Role**: persona pages describe *delivery responsibilities* (process-facing);
  role pages describe *level expectations* (ladder-facing). Link — e.g. persona's career table
  links the role pages; do not copy level tables into persona pages.
- **Member ↔ Role/Persona**: member pages link the role page for their level and the persona
  they embody; competency snapshots reference the role page's expected depth.
- **Artifact ↔ Concept**: the company matrix is declared an implementation of the generic
  career-ladder concept, so patterns and processes stay org-agnostic.

## Generic patterns

1. **Reconciliation, not replacement.** When the framework is revised, re-cluster old categories
   into new differentiation dimensions — nothing dropped, one primary home per competency.
   Keep legacy categories as traceability pages stating their destination, so old links resolve.
2. **Two calibration axes per level.** *Altitude* (qualitative reach: team → domain → area →
   company → industry) and *craft time %* (falls as altitude rises). Every level table carries
   both.
3. **Transitions are first-class.** Each level names what changed from the previous level
   (achieved) and what changes at the next (next), in competency terms — this is what makes
   promotion and growth conversations concrete. Terminal levels omit "next".
4. **Intermediate tiers express scaling pain.** A new rung inserted between two levels means the
   old jump became too wide for the org's size — record it as a full role page, not a footnote.
5. **Craft folds, it doesn't vanish.** On the management track, hands-on craft flattens as craft
   time falls; keep the skill but score it as judgment exercised through the team, with the
   flattening noted for traceability.
6. **Extract legacy per-level documents before refreshing.** Legacy level files carry per-level,
   per-competency behaviors that the new matrix summarizes; parse them into a working extract
   first, then refresh skill pages grouped by competency across all levels and both tracks.

Scale adaptation lives in the cases `README.md` — it applies to every case, not just this one.

## Anti-patterns

- Duplicating level tables in persona pages instead of linking to role pages
- Scoring one competency under two dimensions (breaks calibration)
- Management-track levels without craft-time guidance (managers who stop reviewing entirely)
- Skill pages referencing levels that have no role page — create the page or keep plain text;
  never leave dangling wikilinks
- Letting a re-cluster orphan legacy links — keep traceability pages, keep wikilinks resolving
- Refreshing from the new matrix only, losing the per-level behavioral detail that only exists
  in the legacy documents
