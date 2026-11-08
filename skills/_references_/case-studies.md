---
concept: case-studies
summary: Keep a role-playing skill's posture and heuristics stable in SKILL.md, and capture the many contexts it meets as small, generic case files indexed by a registry, loaded one at a time when the input matches a case's shape.
exemplars: [review-engineering-director, retrospective-3-report, interview-1-preparation]
related: [extensible-dictionary]
---

# Case studies

## Problem

A skill that **adopts a role** (an engineering director, a retro facilitator, an interviewer) must behave consistently across very different inputs: a funding ask, a cost-cut mandate, a new boss, a sailboat retro board, an annual plan. Without structure:

- Every new context gets pasted into `SKILL.md` as another paragraph, until the posture is buried and the file costs tokens on every run.
- The role drifts: each context gets ad-hoc advice instead of the same lens applied the same way.
- Real examples leak names, numbers and internal links into a skill meant to be generic.
- The agent gives the textbook answer even when the situation is the exception, because nothing records *why this one is different*.

## Pattern

Split the skill into a **fixed lens** and a **growing library of contexts**. `SKILL.md` owns the role: posture, voice, the numbered heuristics, the modes and the process. `references/cases/` holds one file per **shape** — a recurring situation or failure pattern — written generically, each pointing back to the heuristics it exercises. A registry (`references/cases/README.md`) indexes shape → file and carries the rules for adding a case. `SKILL.md` says *read the registry, load only the matching case*. New contexts then grow by adding a file and a row; the role itself never changes.

```text
skill-name/
├── SKILL.md                     # Posture, voice, numbered heuristics, modes, process
└── references/
    ├── cases/
    │   ├── README.md            # Registry: shape → file (+ heuristics, guide, template), file contract, growth rules
    │   └── {letter}-{slug}.md   # One shape: frontmatter + fixed body sections
    ├── guides/                  # Optional: theme playbooks grouping several cases
    │   └── {theme}.md
    └── templates/               # Optional: artifacts to produce, paired with cases
        └── {artifact}.md
```

## Use when / Don't use when

**Use when**

- The skill plays a **role with a consistent attitude** that must hold across many contexts or variants.
- Contexts recur as **shapes** (a failure pattern, a format, a situation type) that can be recognised from the input.
- The value of each example is **judgement in prose**: what the weak move looks like, why the usual answer fails here, what to do.

**Don't use when**

- The variation is a mechanical lookup (word → replacement, alias → canonical) → use [extensible-dictionary](./extensible-dictionary.md).
- The variation changes the **process** for a fixed, closed set of modes (e.g. interview steps) → use a **steps registry** of overrides (see `interview-1-preparation/references/steps/`), same registry mechanics, different contract.
- A real team's or person's history is the content → keep it in the vault and point to it; the case library holds only anonymised shapes.

## Anatomy

| Part                                   | Rule                                                                                                                                                                                                                                                                                                                                                 |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Posture + heuristics in `SKILL.md`** | The stable lens. Heuristics are **numbered** so cases can cite them (`heuristics: [18, 3, 7]`) without restating them.                                                                                                                                                                                                                               |
| **Pointer in `SKILL.md`**              | One short section: where the library lives, a one-line summary of each case family, and the loading rule. Never the case content.                                                                                                                                                                                                                    |
| **Registry `cases/README.md`**         | Index table(s): case letter → *shape to match* → heuristics → file → guide/template. Grouped by family when cases differ in kind (e.g. doc-level vs situation-level). Includes the case file contract, provenance (synthetic vs anonymised) and *Growing the library* rules with the **next free letter**.                                           |
| **Case file**                          | Frontmatter: `case`, `name`, `shape`, `heuristics`, optional `guide`/`template`. Fixed body sections so every case reads the same way, e.g. **Before** (weak claim/move) → **Common approach** → **Why this one diverges** → **Interrogation** (challenges, citing heuristic numbers) → **What surfaces** → **Distilled (what to do)** → **Lesson**. |
| **"Why this one diverges"**            | The section that makes cases more than examples: it says when the textbook answer fails, so the role can disagree with the obvious move for a stated reason.                                                                                                                                                                                         |
| **Guides (optional)**                  | A theme playbook (default moves, questions to fire, traps) that groups several cases. Add one when 2+ cases share a theme.                                                                                                                                                                                                                           |
| **Templates (optional)**               | Generic artifacts to produce, each paired with the cases that motivate it.                                                                                                                                                                                                                                                                           |
| **Loading rule**                       | Read the registry, then load **at most one case** (plus at most one guide/template). Never read the library up front or delegate selection to sub-agents.                                                                                                                                                                                            |
| **Genericity rule**                    | No real names, companies, vendors, projects, links or numbers. Systems by category, people by role.                                                                                                                                                                                                                                                  |
| **Promotion rule**                     | A finding that recurs across several cases moves up into a heuristic or a template rule.                                                                                                                                                                                                                                                             |

## Exemplar walkthrough

### `review-engineering-director` — one role, many situations (primary exemplar)

The skill adopts an Engineering Director's posture to review docs and coach leadership situations.

| Part                          | Where it lives                                                                                                                                                                                                                      |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Posture + numbered heuristics | `SKILL.md` → *Posture (non-negotiable)*, *High-Level Judgement Heuristics* (table 1–22)                                                                                                                                             |
| Pointer + loading rule        | `SKILL.md` → *Worked Case Studies* ("load the matching case file only when a claim or situation fits its shape")                                                                                                                    |
| Registry                      | `references/cases/README.md` — two index tables (doc-level A–D, leadership-situation E–S) with heuristics and guide per case; *Heuristic quick map*; *Growing the library* with next letter                                         |
| Case files                    | `references/cases/{a…s}-{slug}.md` — e.g. `f-symmetric-cost-cut.md`: frontmatter with `heuristics`, `guide`, `template`; body Before → Common approach → Why this one diverges → Interrogation → What surfaces → Distilled → Lesson |
| Guides                        | `references/guides/*.md` (cost-and-budget, managing-up, …), each listing its cases                                                                                                                                                  |
| Templates                     | `references/templates/*.md` (exec-cost-review, risk-assessment, …), each paired with cases                                                                                                                                          |

**Why it succeeds:** the director's posture is written once and every case applies it through cited heuristic numbers, so the attitude stays the same whether the input is a promotion packet or a vendor negotiation. The library grew from 4 doc-level cases to 19 cases plus guides and templates; the growth rules say that adding a case does not touch `SKILL.md` (only a new guide does). *Why this one diverges* lets the director push back on the textbook answer with a reason.

### `retrospective-3-report` — one template, many formats

Cases are **worked examples by board format and failure pattern** (sailboat, 4Ls, WRAP, annual plan…). The registry `references/cases/README.md` indexes team → format → pattern → file, separates **synthetic** cases from **anonymised-from-real** ones, and states that a real team's history stays in the vault. Each case shows the format mapping, the review findings and the fixed output against the generic `references/templates/retrospective-report.md`. Rule worth reusing: *add a case only for a new format or failure pattern, not for every real retro*.

### `interview-1-preparation` — the registry as an extension point

Ships an **empty** `references/cases/README.md` registry and a sibling `references/steps/README.md` registry of per-step overrides with a strict *step file contract*. Shows that the registry mechanics (index table + contract + adding rules) work before the first case exists, and how to pick *steps* (process overrides) vs *cases* (contexts).

## Adoption checklist

1. **Write the lens first.** Put posture, voice and **numbered** heuristics in `SKILL.md`. If a heuristic can't be numbered and cited, it isn't stable enough yet.
2. **Collect real inputs** the role has handled. For each, name the **shape** in one line: what would let the agent recognise it in a new input?
3. **Merge variants.** Two inputs with the same shape are one case; the second adds to *What surfaces*. Only a new shape gets a new letter.
4. **Genericise** each case: roles instead of names, categories instead of systems, no numbers or links. Point to the vault for the real history (AGENTS.md step 5).
5. **Fix the case file contract** (frontmatter + body sections) and write it in the registry. Include *Why this one diverges* for situation cases.
6. **Write the registry**: index table(s), provenance, loading rule, *Growing the library* with the next free letter.
7. **Add the pointer section** to `SKILL.md`: location, one line per family, the loading rule. Remove any case content from `SKILL.md`.
8. **Add guides/templates** only when 2+ cases share a theme or an artifact.
9. **Verify:** add a case with only a file + a registry row, trigger the skill on a matching input, and confirm it loads that one case with no `SKILL.md` change.

## Anti-patterns

- **Cases in `SKILL.md`.** Inline examples become a second source of truth and load on every run.
- **One case per real event.** The library becomes a diary; shapes stop being recognisable. Variants go into the existing case.
- **Leaking specifics.** Real names, vendors, dashboards or numbers in a case make the skill non-shareable and anchor the agent on the wrong context.
- **Cases that restate heuristics.** Cite the number; don't copy the rule. One owner per piece of content.
- **Reading the whole library** "to be safe" — defeats progressive disclosure and blurs which shape applies.
- **No "why this one diverges".** The case collapses into the textbook answer and the role can't explain when to deviate.
- **Registry without growth rules.** Without a contract and next letter, new cases drift in structure and the index goes stale.
