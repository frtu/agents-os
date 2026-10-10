---
name: people-ingest
description: >
  Router for people wiki work. Classifies the source or request and runs the
  right step: people-1-structure (career ladders, competencies, processes),
  people-2-member-reports (a direct report mapped to role, level and skills),
  people-3-leaders (profile of a leader, peer or stakeholder, multi-vault).
  Use when the user says "ingest people sources", "process raw/notes/people",
  "add {name} to people", or drops a people-related source without naming a step.
allowed-tools: Bash Read Glob AskUserQuestion Skill
---

# People Ingest (Router)

Routes people sources to one of three steps. The rules live in the sub-skills.

**Shared reference:** `references/people-schema.md` — `wiki/people/` directory layout, page
formats and link conventions (role/skill anchors, naming). Owned here so every step and
`second-brain-lint` reads one copy; load it only when a step or check needs it.

| Step | Skill | Input | Produces |
| --- | --- | --- | --- |
| 1 — Structure | `people-1-structure` | Career ladder, competency framework, process / SDLC docs | `wiki/people/{roles,competencies,processes,steps}/` |
| 2 — Member reports | `people-2-member-reports` | 1:1 notes, feedback, self-assessment for a direct report | `members/{slug}.md` linked to role, skills, steps |
| 3 — Leaders | `people-3-leaders` | Any evidence about a leader, peer or stakeholder | `members/{slug}.md` (+ `{slug}-ref-{topic}.md` in topic vaults) |

Step 2 depends on step 1 (it links to role and skill pages). Step 3 links to step 1's
pages only when relevant.

## Workflow

### 1. Collect the sources

- Files the user named, or
- Unprocessed files: everything under `raw/notes/people/` not listed in `wiki/log.md`.

No sources and no named person → tell the user and stop.

### 2. Classify each source

| Signal | Route |
| --- | --- |
| Levels, tracks, competency definitions, depth progressions, process steps | `/people-1-structure` |
| A named person **in the user's reporting line**, assessed against the ladder (level, growth, feedback) | `/people-2-member-reports` |
| A named person who is a leader, peer or stakeholder; or a `-ref-{topic}` page in a topic vault | `/people-3-leaders` |

If a person's relationship to the user is unclear, ask (direct report vs leader/peer).
Announce the plan in one line, e.g. `2 sources → people-1-structure; Jane Doe → people-2-member-reports`.

### 3. Run in order

1. `/people-1-structure` for all structure sources first.
2. Then `/people-2-member-reports {name}` per direct report. If step 2 reports missing
   role or competency pages and no structure source is at hand, stop and say which are missing.
3. Then `/people-3-leaders {name}` per leader.

### 4. Final report

List per step: pages created / updated, people skipped and why, and the files to stage
with `/change-management-1-stage`.

## Quick Reference

| User says | Route to |
| --- | --- |
| "ingest people sources" / "process raw/notes/people" | full router |
| "ingest this career ladder" / "add these competencies" | `/people-1-structure` |
| "add my report {name}" / "map {name} against the ladder" | `/people-2-member-reports` |
| "create a profile for {name}" / "ref page for {name} in {vault}" | `/people-3-leaders` |
