# AGENTS.md — Skills library

Instructions for any LLM coding agent working in `skills/`, whatever the vendor or harness.

## Stay agent-agnostic

Any LLM must be able to use and maintain these skills. When you write or edit a skill or these docs:

- **Describe actions, not one vendor's tools.** Write "read the file", "run the script", "ask the user" rather than a harness-specific tool name. Shell commands and scripts are the portable layer.
- **Keep the portable core in `SKILL.md`.** `name` + `description` + the Markdown process must be enough on their own. Harness-specific frontmatter (`allowed-tools`, …) is an optional hint other agents ignore; never put rules there.
- **No vendor names or vendor paths** in `SKILL.md`, templates or these docs. Use `<skills-dir>` for the skills directory. Harness-specific paths and behaviour live only in README → *Agent-Specific Setup* and in `link-skills.sh`.
- **`/skill-name` is a convention**, meaning "invoke that skill" (or "follow `skill-name/SKILL.md`" for agents without skill loading).
- A skill whose **subject** is a specific harness (e.g. `claude-permissions-compress`) is fine; say so in its `description`.

## Read first

**Before any change, read [`README.md`](./README.md).** It is the source of truth for:

- **Skills Library** — the catalog: what exists and what each skill does.
- **Skill Dependencies** — the tree + Mermaid graph of which skill invokes or feeds which.
- **Skill Internal Structure & Composition** — folder layout, frontmatter, generic-vs-specific (template + case registry), reuse mechanisms, naming.

Don't duplicate those conventions here or in a skill. If a convention changes, update the README.

## Read mode vs write mode

| Mode | When | Load |
| --- | --- | --- |
| **Read** | You use, run, explain or review a skill without changing it | Its `SKILL.md`, and only the references it says to load. [`_references_/skill-factory.md`](./_references_/skill-factory.md) is optional |
| **Write** | You create a skill, or edit a skill's `SKILL.md`, references, scripts or config | **Required:** [`_references_/skill-factory.md`](./_references_/skill-factory.md) before any change. It holds the step-by-step rules (catalog search, structure, script layering, compose-don't-copy, generic vs specific, README registration, verify, stage) |

In write mode, `skill-factory.md` tells you when to load a design concept from [`_references_/README.md`](./_references_/README.md) (e.g. extensible dictionary, case studies) and, for `scripts/`, the rules in [`_references_/skill-factory-scripts/`](./_references_/skill-factory-scripts/README.md). Load **only** the concept whose symptom matches.

## Known debt

- `second-brain/scripts/relink-wiki.py` and `lint-unformat/scripts/relink-wiki.py` are copies that have drifted apart (`fix-table-wikilinks.py` is still identical). Give each script one owner before changing either.
- `unformat/` is an empty folder with no `SKILL.md`.
