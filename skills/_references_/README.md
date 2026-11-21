# Skill design references — rules & concept library

Reference material for **creating or changing a skill** (write mode). Load in write mode; optional when you only use a skill. This folder is **not a skill** (no `SKILL.md`, never linked by `link-skills.sh`). [`../AGENTS.md`](../AGENTS.md) says when to load it.

## Contents

| File / folder | Kind | Load when |
| --- | --- | --- |
| [`skill-factory.md`](./skill-factory.md) | Process | **Always first** in write mode: the step-by-step rules (understand, search the catalog, design, compose, generic vs specific, register, verify, stage) |
| [`skill-factory-scripts/`](./skill-factory-scripts/README.md) | Rules + concept | The skill has (or should have) a `scripts/` folder: layout, naming, interface, `--help` / `usage.md`, tests, layering, Python & Bash conventions (venv in `~/.cache/{skill}/venv`) |
| [`extensible-dictionary.md`](./extensible-dictionary.md) | Concept | Its symptom matches (concept table below) |
| [`case-studies.md`](./case-studies.md) | Concept | Its symptom matches |
| [`output-template.md`](./output-template.md) | Concept | The skill generates any output (report, page, brief, file): the format lives in a template a human can evolve |

## How to use it

- **Creating a skill** ([`skill-factory.md`](./skill-factory.md) step 3 *Design the structure*): scan the concept table below. If the skill's problem matches a concept's *Use when*, load **that one concept file** and follow its structure and checklist.
- **Improving an existing skill** ([`skill-factory.md`](./skill-factory.md) *Modifying an existing skill*): look for the symptom in the *Symptom it fixes* column — e.g. "`SKILL.md` is edited every time a new word appears" — and apply the matching concept.
- **Progressive disclosure applies here too:** read this README, then load only the file(s) that match. Never read the whole folder up front.

The folder layout, frontmatter and reuse order in [`../README.md`](../README.md) → *Skill Internal Structure & Composition* remain the source of truth. Files here go one level deeper: *how* to build a skill and *why* a structure works, with working exemplars.

## Concepts

Each concept is one file that names a pattern, says when to use it, and points to a **real skill in this library that already applies it successfully**, so you copy a proven structure, not an idea.

| Concept               | Symptom it fixes                                                                                           | Use when                                                                                                  | Exemplar skill(s)                                                                  | File                                                     |
| --------------------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------- |
| Extensible dictionary | `SKILL.md` is edited every time a new word, alias or mapping appears; users answer the same question twice | Lookup data grows with use and a script can apply it directly, no LLM (the agent only grows it)          | `lint-transcript-normalise`, `transcribe-voice-memo` (outcome-calibrated)          | [`extensible-dictionary.md`](./extensible-dictionary.md) |
| Case studies          | A role-playing skill drifts across contexts, or `SKILL.md` swells with one paragraph per new situation     | A skill adopts a consistent attitude across many recurring shapes (situations, formats, failure patterns) | `review-engineering-director`, `review-product-strategy`, `retrospective-3-report`, `people-ingest`, `interview-1-preparation` | [`case-studies.md`](./case-studies.md)                   |
| Output template       | Changing a heading, section or column means editing `SKILL.md` or code; each run reads the format differently | The skill generates a document, page, brief or file that someone reads, keeps or owns | `review-engineering-director`, `retrospective-3-report`, `interview-1-preparation`, `second-brain-ingest-advanced` (script-filled) | [`output-template.md`](./output-template.md) |
| Script layering       | The agent redoes mechanical steps by hand each run; `SKILL.md` describes loops and conditions in prose; only an agent can run the skill | A step is deterministic (same input → same output), runs in a sequence with checks, or a human should be able to run it too | `pdf-extract`, `second-brain-ingest-advanced`, `lint-unformat` | [`skill-factory-scripts/script-layering.md`](./skill-factory-scripts/script-layering.md) |

## Concept file contract

Every concept file has these sections, in this order:

| Section                       | Content                                                                                                                  |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Frontmatter**               | `concept` (slug = file name), `summary` (one line), `exemplars` (list of skill folders), `related` (other concept slugs) |
| **Problem**                   | The recurring pain, phrased as the symptom an agent or user notices                                                      |
| **Pattern**                   | The structural answer in 3–5 sentences, plus a folder/file sketch                                                        |
| **Use when / Don't use when** | Decision criteria, including the neighbouring concept to pick instead                                                    |
| **Anatomy**                   | The parts of the pattern and the rule each part follows                                                                  |
| **Exemplar walkthrough**      | Where the real skill implements each part (file paths, section names), and what makes it succeed                         |
| **Adoption checklist**        | Numbered steps to apply the concept to a new or existing skill                                                           |
| **Anti-patterns**             | The failure shapes seen when the pattern is applied badly                                                                |

`skill-factory.md` and `skill-factory-scripts/rules.md` are rules, not concepts, so they don't follow this contract.

## Adding a concept

1. Confirm it is **atomic** (one pattern, one problem) and **proven**: at least one skill in this library applies it and works. No exemplar → no concept yet.
2. Write `{concept-slug}.md` here (or in the topic sub-folder it belongs to, e.g. `skill-factory-scripts/`) following the contract above. Keep it generic: point to the exemplar skill's files instead of pasting their content (one owner per piece of content).
3. Add one row to the concept table and, if it's a new file or folder at this level, to *Contents*.
4. If the concept changes how skills should be built by default, update `../README.md` → *Skill Internal Structure & Composition* instead of (or in addition to) adding a file here — the README stays the source of truth for conventions.
