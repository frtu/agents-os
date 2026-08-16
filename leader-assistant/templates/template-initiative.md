# Template: Initiative Page

Copy this template to `wiki/projects/{domain}/initiative-{name}.md` and fill in placeholders.

Use this to **bootstrap any initiative** in the `projects` (EXECUTION) vault — a long-running theme that delivers a long-term goal through a **collection of projects**.

## Taxonomy: Initiative vs Project

| Concept | Definition | Time horizon | Delivery | Page |
|---------|-----------|--------------|----------|------|
| **Initiative** | A long-running **theme** pursuing a long-term goal (north star). Broken down into a collection of projects. | Open-ended / multi-quarter | Achieved incrementally as its projects land | `initiative-{name}.md` · `# Initiative:` · `Category: initiative` |
| **Project** | A **time-bounded** unit of work with a precise delivery date and a concrete achievement. | Bounded (weeks–a quarter) | One shipped outcome by a target date | `project-{name}.md` · `# Project:` · `Category: project` |

**Containment:** an initiative *is* its projects. It has no delivery of its own — it advances only as the projects in its **Projects** collection reach `✅`. Each project row here should have its own `project-{name}.md` page (which feeds the weekly digest); this initiative page aggregates them.

> Use this template for the **initiative**. For a single time-bounded project, create a `project-{name}.md` page using the vault's project conventions and link it from the **Projects** table below.

## Design principle: output-driven, human-maintainable

This page is organized around **outputs, not activity**. Every section answers *"what will exist when this is done, and where are we against it?"* — not *"what did we work on."* For an initiative, the output is **delivered projects**, so the Projects table is the spine. Two consequences shape how you fill it:

- **The LLM writes projects, decisions, and status** — concrete, verifiable units, never a narrative of effort.
- **A human keeps it current in under a minute.** The scannable status block sits at the top; the append-only **Updates** log at the bottom is the only place that grows over time. Everything in between is *replaced in place*, so the page never becomes a diary a reviewer has to read end-to-end.

Each section below carries an **update trigger** in the fill guide — the event that means "touch this section now." If nothing triggered it, leave it alone.

---

## The template

```markdown
---
Category: initiative
Tags:
  - initiative/{status}/{domain}
  - {topic}
Owner: {Person}
Status: {On Track | At Risk | Blocked | Complete}
Health: {green | yellow | red}
Horizon: {long-term target, e.g. FY26 or H2 2026}
sources:
  - {source-file-or-link}
Created: {YYYY-MM-DD}
Last Updated: {YYYY-MM-DD}
---

# Initiative: {Name}

{One sentence: the long-term goal this initiative pursues and for whom.}

## At a Glance

| Field | Value |
|-------|-------|
| **Status** | {On Track / At Risk / Blocked / Complete} |
| **Health** | {🟢 on track / 🟡 blockers / 🔴 blocked} |
| **Owner** | {Person} |
| **Horizon** | {long-term target} |
| **Progress** | {N of M projects delivered} |

## Objective (North Star)

**Problem:** {The systemic gap or pain this initiative closes.}
**Long-term outcome:** {The end-state that exists when the theme is fully realized — a result, not a task.}
**Why now:** {The constraint, mandate, or opportunity driving the timing.}

## Success Criteria

Long-term signals that the north star was actually reached (distinct from "projects shipped" —
these prove the theme paid off).

- {Metric or observable, with a target: e.g. P99 < 1s org-wide, adopted by all 8 domains, 0 rollbacks/quarter}
- {…}

## Projects

The collection — the initiative's output-driven spine. Each row is a **time-bounded** project
with a precise delivery date and a concrete achievement. The initiative advances only as rows
reach `✅`. Give each its own `project-{name}.md` page and link it.

| Project | Achievement (definition of done) | Delivery | Status | Page |
|---------|----------------------------------|----------|--------|------|
| {Name} | {Verifiable shipped outcome} | {date} | {☐ / ◐ / ✅} | [[project-{name}\|{Name}]] |
| {Name} | {…} | {date} | {☐} | [[project-{name}\|{Name}]] |

## Roadmap

Sequencing of the projects across the horizon (waves/phases). Keep dates honest — move them
here, don't delete them.

| Phase / Wave | Projects | Target | Status |
|--------------|----------|--------|--------|
| 1 | {which projects} | {date} | {☐ / ◐ / ✅} |
| 2 | {…} | {date} | {☐} |

## Scope

**In scope:** {The themes/projects this initiative owns.}
**Out of scope:** {Explicitly excluded — the guardrail that prevents creep into adjacent initiatives.}

## People

| Role | Who | Responsibility |
|------|-----|----------------|
| **Owner** | {Person} | {Accountable for the initiative} |
| **Sponsor** | {Person} | {Exec/stakeholder backing it} |
| **Project leads** | {People} | {Who owns which project} |
| **Stakeholder** | {Person / team} | {What they review or need} |

## Decisions

Append-only, dated. One line per decision + the reasoning kept, so a reviewer sees *why*
without archaeology. Promote weighty ones to an ADR in `wiki/synthesis/`.

- **{YYYY-MM-DD}** — {Decision}. *Because:* {reason}. *Rejected:* {alternative, if any}.

## Risks & Blockers

| Risk / Blocker | Impact | Mitigation / Next step | Owner | Status |
|----------------|--------|------------------------|-------|--------|
| {What could stop a project or the theme} | {H/M/L} | {The move that clears it} | {Person} | {Open / Mitigated / Closed} |

## Weekly Signal {optional}

Read by the weekly digest. Set only when this initiative should roll up differently than its
own name.

- **Report Under:** {flagship alias, if this folds into a parent/sibling initiative}
- **This week:** {the single line worth reporting — a project that shipped or a real blocker}

## Updates

Append-only, newest first. Each entry is a dated **delta** — what changed since last time,
not a status restatement. This is the only section that grows.

- **{YYYY-MM-DD}** — {Which project shipped / what was decided / what blocked since the last update.}

## Related

- [[{portfolio-or-goal}|{Name}]] — parent portfolio / strategic goal
- [[{concept-page}|{Name}]] — reference concept (link to search / eng-department wiki)
- [[{sibling-initiative}|{Name}]] — related initiative
```

---

## How to fill it correctly

Apply editorial judgment first — cut sections a small initiative doesn't need (see Minimal
variant), keep the rest tight. Then follow the per-section rules and **update triggers**.

### Frontmatter

- **`Tags`** — first tag is always `initiative/{status}/{domain}` where status is
  `active` / `paused` / `done` and domain matches the folder (e.g. `initiative/active/search`).
  Constituent **project** pages use the `project/{status}/{domain}` tag instead.
- **`Status` / `Health`** are the audience-facing summary. Keep them in sync with the
  **At a Glance** block and with the Projects statuses — Health is 🟢 by default for an
  initiative that is progressing; reserve 🟡/🔴 for a real, worth-communicating blocker, **not**
  for "some projects still open."
- **`Horizon`** — the long-term target (a fiscal year, a half). Unlike a project's `Target`,
  this is not a single delivery date; the deliveries live in the Projects rows.
- **`Last Updated`** — bump it every time you touch the page. *Update trigger: any edit.*

### At a Glance
*Update trigger: whenever a project's status changes.* This is the block a human reads first —
it must be true at a glance or the whole page loses trust. Mirror the frontmatter; don't let
them drift. **Progress** counts delivered projects (`N of M`), not tasks.

### Objective (North Star)
*Update trigger: rarely — only if the initiative's reason-for-being changes.* State the
long-term outcome as a **result** ("search P99 under 1s across all domains"), never as an
activity ("work on latency"). If you can't write the long-term outcome, the initiative isn't
ready to bootstrap.

### Success Criteria
*Update trigger: set once at bootstrap; revisit only if targets are renegotiated.* These prove
the *theme* paid off, distinct from "we shipped the projects." Prefer a number and a
beneficiary. Empty success criteria = an unfalsifiable initiative.

### Projects
*Update trigger: a project is added, changes status, or is delivered.* This table is the spine.
Rules:
- Each project is **time-bounded** — it has a precise **Delivery** date and one concrete
  **Achievement** (definition of done). If it has no delivery date, it's not a project yet.
- **Achievement is verifiable** — someone other than the lead can confirm it ("in prod,
  serving traffic"), not "mostly done."
- Status markers: `☐` not started · `◐` in progress · `✅` delivered. Flip status **here first**,
  then reflect it up into At a Glance / frontmatter.
- **Give each project its own page** (`project-{name}.md`, `# Project:`, `Category: project`)
  — that page carries the project's own deliverables/milestones and feeds the weekly digest.
  Link it in the **Page** column; leave the link plain text until the page exists (Rule 22).

### Roadmap
*Update trigger: a wave completes, or a date slips.* When a date moves, **change it in place**
and note the slip in Updates — never silently delete a missed target. Group projects into
phases/waves that show how the theme unfolds over the horizon.

### Scope
*Update trigger: when someone asks "does this initiative also cover X?".* The **Out of scope**
line earns its keep at the initiative level — it's the boundary against overlapping adjacent
initiatives.

### People
*Update trigger: someone joins, leaves, or changes role.* One accountable **Owner**; name the
**Sponsor** and which lead owns which project. If there are two owners, there are zero.

### Decisions
*Update trigger: a decision is made that a future reader would otherwise have to reverse-
engineer.* One dated line, with **Because** (reasoning) and **Rejected** (the road not taken).
Append-only. A decision that reshapes architecture graduates to an ADR page in
`wiki/synthesis/` (per wiki-schema Rule 26) — link it here rather than restating.

### Risks & Blockers
*Update trigger: a risk emerges, its status changes, or it clears.* Frame the **Next step** as
the concrete move that clears the blocker, with an owner and a status — not a description of
the problem. Close rows (don't delete) so the history of what threatened delivery stays legible.

### Weekly Signal
*Update trigger: before the weekly digest, if this initiative rolls up under a flagship.* The
weekly skill reads `Report Under:` to fold sibling/child efforts into the name the audience
recognizes. Note that the digest primarily reads the individual **project** pages; set this
only when the initiative itself is the reporting unit. Leave it out for standalone themes.

### Updates
*Update trigger: any meaningful change — the running heartbeat of the page.* Newest first.
Each entry is a **delta**: which project shipped, what was decided, what broke *since the last
entry* — never a full status restatement (that's what At a Glance is for). This is the section
a reviewer skims to catch up; keep entries to one line where possible.

### Related
*Update trigger: when a new dependency or reference concept appears.* Before linking, resolve
concepts against the existing wiki (`search`, `workflow`, `engineering-department` portals) per
the vault CLAUDE.md — reference existing `[[link-value]]` pages rather than restating them.
Unresolved names stay **plain text** (wiki-schema Rule 22).

---

## Minimal Initiative Page

For a young or narrow initiative — drop Roadmap, People, Decisions, Weekly Signal, and Risks
until they're actually needed. Keep the north star, the projects collection, and the log.

```markdown
---
Category: initiative
Tags:
  - initiative/active/{domain}
Owner: {Person}
Status: On Track
Health: green
Horizon: {long-term target}
Created: {YYYY-MM-DD}
Last Updated: {YYYY-MM-DD}
---

# Initiative: {Name}

{One sentence: the long-term goal this pursues and for whom.}

## At a Glance

| Field | Value |
|-------|-------|
| **Status** | On Track |
| **Health** | 🟢 |
| **Owner** | {Person} |
| **Horizon** | {long-term target} |

## Objective (North Star)

**Long-term outcome:** {The end-state that exists when the theme is realized.}

## Projects

| Project | Achievement | Delivery | Status | Page |
|---------|-------------|----------|--------|------|
| {Name} | {…} | {date} | {☐} | [[project-{name}\|{Name}]] |

## Updates

- **{YYYY-MM-DD}** — {What changed.}

## Related

- [[{portfolio-or-goal}|{Name}]] — parent portfolio / strategic goal
```
```
