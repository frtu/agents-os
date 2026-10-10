---
name: people-2-member-reports
description: >
  Step 2 of people-ingest. Create or update a direct report's member page and
  anchor it in the people structure: role page for their track and level,
  competency/skill pages with expected vs observed depth, growth actions toward
  the next level, and the process steps they contribute to. Use when the user
  says "add my report {name}", "update {name}'s page from this 1:1", "map
  {name} against the ladder", or drops 1:1 notes, feedback or a self-assessment
  for someone in their reporting line. Needs the structure pages from
  people-1-structure; leaders, peers and stakeholders go to people-3-leaders.
allowed-tools: Bash Read Write Edit Glob Grep
risk-level: low
---

# People 2 — Member Reports

Create or update the member page of a **direct report** (someone assessed against
the career ladder) and link it into the structure built by `/people-1-structure`:
role (track + level) → competencies/skills → process steps.

**References (load when needed):**
- `references/templates/member-report.md` — page skeleton and per-section guidance (step 3)
- `people-ingest/references/people-schema.md` — role/skill/step page formats and the
  link formats (section anchors, `role-{track}-{level}`) to reuse (step 2)
- `people-3-leaders/SKILL.md` § *Fill rule: evidence-bounded* — evidence rules this step
  applies as-is (step 4)

## 1. Gather inputs

1. **The person** — full name, slug (kebab-case), aliases.
2. **Role** — track (IC / M) and level, from the user or the source. Never guess a level.
3. **Evidence** — files read this session, `raw/notes/people/members/**` and other `raw/**`
   matches for the name (1:1 notes, feedback, self-assessments, review notes).
4. **Existing page** — `wiki/people/members/{slug}.md`. If it exists, this is an update:
   keep its structure, append evidence, update `Last Updated`.

## 2. Resolve the structure pages

```bash
ls wiki/people/roles/ wiki/people/competencies/ wiki/people/steps/ 2>/dev/null
```

- Find `role-{track}-{level}.md`. **If the role or competency pages are missing, stop**
  and propose `/people-1-structure` first — this step links to the ladder, it does not
  invent it.
- From the role page read: *Competency Expectations* (expected depth per skill),
  *Key {Level} → {Next} Transitions*, *What Good Looks Like*.
- For each skill the evidence touches, read its skill page: *Measurement Indicators*,
  *Red Flags*, *Growth Actions*, *SDLC Application*.

## 3. Pick the template

- Vault already has direct-report pages → read 2–3, follow their majority conventions.
- Otherwise use `references/templates/member-report.md`.

State the skeleton in one line before writing.

## 4. Fill — evidence-bounded

Apply the fill rule and evidence hygiene from `people-3-leaders/SKILL.md`
(cite every claim, gap-mark or omit what has no evidence, label inference). Specific to
direct reports:

- **Expected depth** comes from the role page, **observed depth** from the evidence only.
  No evidence for a skill → leave *Observed* blank, don't copy *Expected*.
- **Gaps** = observed below expected, or a skill-page *Red Flag* seen in the evidence.
- **Growth actions** come from the skill page's *Growth Actions* row for the current →
  next level, and the role page's *Key transitions (next)*. Don't write generic advice.
- **Sensitive content** — no ratings, compensation, health or personal matters unless the
  user asks for them explicitly.

## 5. Link

| From member page to | Format |
| --- | --- |
| Role | `[[role-{track}-{level}\|{Level} — {Title}]]` |
| Skill | `[[{skill}#IC Track Depth Progression\|{Skill Name}]]` (or `#M-Track …`) |
| Step | `[[step-{name}\|{Step Name}]]` |
| Manager / peers | `[[{slug}]]` only if the page exists, else plain text |

Escape `|` as `\|` inside tables. Links are one-way: don't edit role or skill pages to
list members (Obsidian backlinks cover it).

## 6. Portal & log

- `wiki/portal.md` → `### Members`: `- [[{slug}|{Name}]] — {Level} {Title}, {team}`
- `wiki/log.md` (append): `## [YYYY-MM-DD] people-2-member-reports | {Name}` + created/updated, sources used.

## 7. Validate & report

- [ ] Role page exists and is linked; level is from a source, not a guess
- [ ] Every skill link uses a section anchor and resolves
- [ ] Observed depth and gaps each cite evidence; unknowns blank or gap-marked
- [ ] Growth actions trace to a skill page or the role page
- [ ] No placeholder text (`{Name}`, `TBD`) left in prose
- [ ] Portal and log updated

Report: role/level used · skills assessed vs left blank · gaps and growth actions ·
missing structure pages · files to stage with `/change-management-1-stage`.
