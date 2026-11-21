# Skill factory — rules for creating or changing a skill

**Load this file in write mode only**: when you create a skill, or edit a skill's `SKILL.md`, references, scripts or config. When you only **use** (run, read, explain) a skill, loading it is optional.

It builds on the library [`README.md`](../README.md) → *Skill Internal Structure & Composition*, which stays the source of truth for folder layout, frontmatter, generic-vs-specific and reuse order. This file is the **process**; the README is the **convention**; the concept files next to this one (indexed in [`./README.md`](./README.md)) are the **patterns**.

## Creating or changing a skill

Work through these steps in order. Stop and ask the user if a step turns up a real design choice (e.g. extend vs create).

### 1. Understand the ask

- What job does the skill do, what does it take in, what does it produce, and who reads the output?
- Is there a sample input or a real example (a clipping, a doc, a transcript)? Read it fully. It becomes the first **case**, and the **template** is generalized from it.

### 2. Search the catalog before creating

Check the README catalog and dependency graph, then decide:

| Finding | Action |
| --- | --- |
| An existing skill already does it | Don't create. Use it, or add a mode or case to it |
| An existing skill does part of it | Create the new skill and **invoke** the existing one for that part |
| Same structure, different subject (another team, another doc type) | Add a **case** to the existing skill's registry, not a new skill |
| Nothing close | Create a new skill |

### 3. Design the structure

Follow README → *Skill Internal Structure & Composition*:

- `SKILL.md`: frontmatter (`name` = folder name; `description` = what + when + trigger phrases + how it differs from its neighbours; optional `allowed-tools` hint), then the process.
- **Every generated output → a template** in `references/templates/{artifact}.md`, so a human can evolve the format without changing the skill. `SKILL.md` and scripts only select and fill it. Follow [`output-template.md`](./output-template.md) (agent-filled skeleton vs script-filled `{{PLACEHOLDER}}`, what stays in code as a machine contract).
- Specific instances → `references/cases/{letter}-{slug}.md` + `references/cases/README.md` registry.
- **Deterministic work → `scripts/`, layered.** Any step that gives the same output for the same input (parse, transform, check, move, count) is a script, not prose for the agent to redo. Follow [`skill-factory-scripts/rules.md`](./skill-factory-scripts/rules.md) (rules) and [`skill-factory-scripts/script-layering.md`](./skill-factory-scripts/script-layering.md) (pattern):
  - **Atomic utils**: one small, reusable action per function or script, each with a `test_*.py` next to it.
  - **Orchestration script** (optional, per use case): a deterministic sequence of utils with the loops, conditions and checks (`for` each file, skip if up to date, stop on error). `SKILL.md` then only calls the entry point.
  - **Operable by agent or human**: every script explains itself through `--help`. Add `references/usage.md` when `--help` is not enough (output format, statuses, exit codes, env vars, agent contract).
- **Secrets and configuration** → env vars `{SKILL}_{THING}`; secrets follow [`secret-configuration.md`](./secret-configuration.md) (env var, optional `.env`, `references/.env.example`, explicit override, never guessed).
- **Progressive disclosure:** `SKILL.md` says which reference to load and when. Never "read everything up front".
- Scan the concept table in [`README.md`](./README.md) and load **only** the concept whose *Use when* matches.

### 4. Compose, don't copy

Choose the reuse mechanism in the README's order: **invoke sub-skill → router + numbered steps → division of labour → point to the owning skill's reference → copy (last resort, with a `keep in sync` header)**.

- Each piece of content has **one owner**. If you're about to paste another skill's rules, template or script, invoke it or link to it instead.
- Only reuse **when relevant**. Don't add a dependency for a trivial overlap.
- Name the hand-off explicitly in the new skill (*"run `/rewrite-clarity` next"*). If the skill invokes others automatically, say so in the process (and add the harness's skill-invocation tool to the optional `allowed-tools` hint, e.g. `Skill`).

### 5. Keep generic and specific apart

- Templates and `SKILL.md` contain **no** team names, internal systems, URLs or real numbers. Those go in `references/cases/` (see [`output-template.md`](./output-template.md) → *Generic only*).
- Genericize the source example: turn its specifics into section guidance and questions, and keep the specifics themselves in the case file.
- Don't copy internal links (dashboards, wiki URLs) from source material into the skill. Point to the source file in the vault instead.

### 6. Register the skill in the README

In the same change, update:

1. **Skills Library** — one bullet under the right category (plus a usage example if the invocation isn't obvious).
2. **Skill Dependencies** — the tree and the Mermaid graph, one edge per invoke or link.
3. **Recommendation** / **Common Workflows** — only if the skill belongs in a recommended link set.
4. **Environment Variables** — if the skill reads any.

### 7. Verify

- `name` matches the folder name; the frontmatter parses; every `references/` path mentioned in `SKILL.md` exists.
- Outputs: each generated document has a template, and `SKILL.md` doesn't restate its sections ([`output-template.md`](./output-template.md) → *Adoption checklist* step 7).
- Scripts: run their tests, and run the checklist in [`skill-factory-scripts/rules.md`](./skill-factory-scripts/rules.md) §9 (`--help`, `--dry-run`, no prompts).
- Every dependency edge in the README matches a real reference in a `SKILL.md`. Check with `grep -rn '/{skill}' */SKILL.md`; don't draw edges from memory.
- Optionally `./link-skills.sh {name} [harness]` and trigger the skill once with a real input. If you changed `link-skills.sh`, run `./test-link-skills.sh`.

### 8. Stage

- The root `.gitignore` ignores `SKILL.md`: use `git add -f {name}/SKILL.md`.
- Stage by explicit path (never `git add .`), then hand off to `/change-management-1-stage` → `/change-management-9-log`. **Never commit** unless the user asks.

## Modifying an existing skill

- Read its `SKILL.md` and the references it loads before editing.
- New subject or new failure shape → add a case + registry row. Leave `SKILL.md` alone unless the process changes.
- A finding that recurs across cases → promote it to a generic rule in the template.
- A format change (heading, section, column, tone) → edit the template only. If you have to touch `SKILL.md` or a script to change the format, extract it into a template first ([`output-template.md`](./output-template.md)).
- The agent keeps redoing the same mechanical step by hand → extract it into a util in `scripts/` (and into the orchestrator if it runs in sequence with others).
- If you change a skill's trigger, outputs or hand-offs, check the skills that depend on it (README dependency graph) and update the README.
