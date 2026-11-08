# Skill design references — concept library

Atomic, reusable **design concepts** for building or improving a skill. Each concept is one file that names a pattern, says when to use it, and points to a **real skill in this library that already applies it successfully** — so you copy a proven structure, not an idea.

This folder is **not a skill** (no `SKILL.md`, never linked by `link-skills.sh`). It is reference material for agents following [`../AGENTS.md`](../AGENTS.md) and humans designing skills.

## How to use it

- **Creating a skill** (AGENTS.md step 3 *Design the structure*): scan the concept table below. If the skill's problem matches a concept's *Use when*, load **that one concept file** and follow its structure and checklist.
- **Improving an existing skill** (AGENTS.md *Modifying an existing skill*): look for the symptom in the *Symptom it fixes* column — e.g. "`SKILL.md` is edited every time a new word appears" — and apply the matching concept.
- **Progressive disclosure applies here too:** read this README, then load only the concept(s) that match. Never read the whole folder up front.

The folder layout, frontmatter and reuse order in [`../README.md`](../README.md) → *Skill Internal Structure & Composition* remain the source of truth. Concepts here go one level deeper: *why* a structure works and *how* to adopt it, with a working exemplar.

## Concepts

| Concept | Symptom it fixes | Use when | Exemplar skill(s) | File |
| ------- | ---------------- | -------- | ----------------- | ---- |
| Extensible dictionary | `SKILL.md` is edited every time a new word, alias or mapping appears; users answer the same question twice | Lookup data grows with use and can be matched by rules a script applies | `lint-transcript-normalise` | [`extensible-dictionary.md`](./extensible-dictionary.md) |
| Case studies | A role-playing skill drifts across contexts, or `SKILL.md` swells with one paragraph per new situation | A skill adopts a consistent attitude across many recurring shapes (situations, formats, failure patterns) | `review-engineering-director`, `retrospective-3-report`, `interview-1-preparation` | [`case-studies.md`](./case-studies.md) |

## Concept file contract

Every concept file has these sections, in this order:

| Section | Content |
| ------- | ------- |
| **Frontmatter** | `concept` (slug = file name), `summary` (one line), `exemplars` (list of skill folders), `related` (other concept slugs) |
| **Problem** | The recurring pain, phrased as the symptom an agent or user notices |
| **Pattern** | The structural answer in 3–5 sentences, plus a folder/file sketch |
| **Use when / Don't use when** | Decision criteria, including the neighbouring concept to pick instead |
| **Anatomy** | The parts of the pattern and the rule each part follows |
| **Exemplar walkthrough** | Where the real skill implements each part (file paths, section names), and what makes it succeed |
| **Adoption checklist** | Numbered steps to apply the concept to a new or existing skill |
| **Anti-patterns** | The failure shapes seen when the pattern is applied badly |

## Adding a concept

1. Confirm it is **atomic** (one pattern, one problem) and **proven**: at least one skill in this library applies it and works. No exemplar → no concept yet.
2. Write `{concept-slug}.md` here following the contract above. Keep it generic: point to the exemplar skill's files instead of pasting their content (one owner per piece of content).
3. Add one row to the table above.
4. If the concept changes how skills should be built by default, update `../README.md` → *Skill Internal Structure & Composition* instead of (or in addition to) adding a file here — the README stays the source of truth for conventions.
