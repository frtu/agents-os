# AGENTS.md — Skills library

Instructions for any coding agent (Claude Code, Codex, Cursor, Gemini…) working in `skills/`.

## Read first

**Before any change, read [`README.md`](./README.md).** It is the source of truth for:

- **Skills Library** — the catalog: what exists and what each skill does.
- **Skill Dependencies** — the tree + Mermaid graph of which skill invokes or feeds which.
- **Skill Internal Structure & Composition** — folder layout, frontmatter, generic-vs-specific (template + case registry), reuse mechanisms, naming.

Don't duplicate those conventions here or in a skill. If a convention changes, update the README.

## Skill factory — creating or changing a skill

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

- `SKILL.md`: frontmatter (`name` = folder name; `description` = what + when + trigger phrases + how it differs from its neighbours; `allowed-tools`), then the process.
- Generic output structure → `references/templates/{artifact}.md` (insight / style & format / questions to answer per section).
- Specific instances → `references/cases/{letter}-{slug}.md` + `references/cases/README.md` registry.
- Deterministic transforms → `scripts/` with a `test_*.py` next to each script.
- **Progressive disclosure:** `SKILL.md` says which reference to load and when. Never "read everything up front".

### 4. Compose, don't copy

Choose the reuse mechanism in the README's order: **invoke sub-skill → router + numbered steps → division of labour → point to the owning skill's reference → copy (last resort, with a `keep in sync` header)**.

- Each piece of content has **one owner**. If you're about to paste another skill's rules, template or script, invoke it or link to it instead.
- Only reuse **when relevant**. Don't add a dependency for a trivial overlap.
- Name the hand-off explicitly in the new skill (*"run `/rewrite-clarity` next"*). Add `Skill` to `allowed-tools` if the skill invokes others automatically.

### 5. Keep generic and specific apart

- Templates and `SKILL.md` contain **no** team names, internal systems, URLs or real numbers. Those go in `references/cases/`.
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
- Scripts: run their tests.
- Every dependency edge in the README matches a real reference in a `SKILL.md`. Check with `grep -rn '/{skill}' */SKILL.md`; don't draw edges from memory.
- Optionally `./link-skills.sh {name}` and trigger the skill once with a real input.

### 8. Stage

- The root `.gitignore` ignores `SKILL.md`: use `git add -f {name}/SKILL.md`.
- Stage by explicit path (never `git add .`), then hand off to `/change-management-1-stage` → `/change-management-9-log`. **Never commit** unless the user asks.

## Modifying an existing skill

- Read its `SKILL.md` and the references it loads before editing.
- New subject or new failure shape → add a case + registry row. Leave `SKILL.md` alone unless the process changes.
- A finding that recurs across cases → promote it to a generic rule in the template.
- If you change a skill's trigger, outputs or hand-offs, check the skills that depend on it (README dependency graph) and update the README.

## Known debt

- `second-brain/scripts/relink-wiki.py` and `lint-unformat/scripts/relink-wiki.py` are copies that have drifted apart (`fix-table-wikilinks.py` is still identical). Give each script one owner before changing either.
- `unformat/` is an empty folder with no `SKILL.md`.
