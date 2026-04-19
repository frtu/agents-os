---
name: people-ingest
description: >
  Process people-related sources (career ladders, competencies, processes) into
  structured wiki pages. Use when the user adds career ladder files, skill frameworks,
  SDLC documents, or team member info to raw/notes/people/ and wants them ingested
  with proper cross-linking between roles, skills, and processes.
allowed-tools: Bash Read Write Edit Glob Grep
---

# People Ingest

Process people-related source documents into structured, interlinked wiki pages under `wiki/people/`.

**Schema Reference:** Read `references/people-schema.md` for complete page formats and conventions.

## Identify Sources to Process

Determine which files need ingestion:

1. If the user specifies files, use those
2. If the user says "process people sources" or similar, detect unprocessed files:
   - List all files in `raw/notes/people/` and subdirectories
   - Read `wiki/log.md` and extract previously ingested source filenames
   - Any file in `raw/notes/people/` not listed in the log is unprocessed
3. If no unprocessed files are found, tell the user

## Content Categories

People content maps to these wiki directories:

| Source Content | Wiki Location | Naming Pattern |
|----------------|---------------|----------------|
| Career ladder levels | `wiki/people/roles/` | `role-ic-{level}.md` or `role-mgmt-{level}.md` |
| Career ladder overview | `wiki/people/roles/` | `engineering-career-ladder.md` |
| Competency categories | `wiki/people/competencies/` | `{category}.md` |
| Individual skills | `wiki/people/competencies/` | `{skill-name}.md` |
| Processes (SDLC, etc.) | `wiki/people/processes/` | `{process-name}.md` |
| Process steps | `wiki/people/steps/` | `step-{name}.md` |
| Team members | `wiki/people/members/` | `{name}.md` |

## Process Each Source

For each source file, follow this workflow:

### 1. Read and categorize the source

Read the entire file and identify:
- **Type**: Career ladder? Competency framework? Process definition? Member profile?
- **Scope**: Single role? Multiple roles? Single skill? Skill category?
- **Track**: IC only? M only? Both tracks?

### 2. Discuss key takeaways

Before writing, share 3-5 key takeaways:
- For career ladders: levels covered, key competencies, track progression
- For competencies: skills covered, depth progression, measurement indicators
- For processes: steps involved, skills applied, workflow structure

Wait for user confirmation before proceeding.

### 3. Create or update wiki pages

**For Career Ladder Sources:**

1. Create/update role pages following the Role Page format in `references/people-schema.md`
2. Include Level Differentiation section with:
   - Comparison table (← previous, → next)
   - Focus areas for this level
   - Key transitions achieved and next
3. Create 3-column competency tables:
   - Competency (with section anchor: `[[skill#IC Track Depth Progression|Skill Name]]`)
   - Depth (bold indicator)
   - Expectations
4. Update `engineering-career-ladder.md` overview page

**For Competency/Skill Sources:**

1. Create category page if new category
2. Create/update individual skill pages with:
   - IC Track Depth Progression table
   - M-Track Depth Progression table (if applicable)
   - Measurement Indicators table
   - Red Flags section
   - Growth Actions table
   - SDLC Application section
3. Link skills to roles using `[[role-{track}-{level}|{Level}]]` format

**For Process Sources:**

1. Create/update process page with steps overview
2. Create/update step pages linking to:
   - Skills applied in that step
   - Previous/next steps
   - Parent process
3. Update skill pages' SDLC Application sections

### 4. Enrich existing pages

When processing new sources, also update related existing pages:

**Cross-link roles and skills:**
- In role pages: add skill links with section anchors
- In skill pages: add role references in depth progression tables

**Cross-link processes and skills:**
- In skill pages: update SDLC Application section
- In step pages: update Skills Applied section

**Update category pages:**
- Add new skills to category skill tables

### 5. Update wiki/portal.md

Add entries under **People** section:

```markdown
### Roles
- [[role-ic-3|Senior Software Engineer]] — Feature ownership with cross-team influence

### Competencies
- [[coding-expertise|Coding Expertise]] — Delivering value through code

### Processes
- [[software-development-lifecycle|Software Development Lifecycle]] — End-to-end delivery process

### Steps
- [[step-design|Design]] — Technical and solution design phase
```

### 6. Update wiki/log.md

Append:

```markdown
## [YYYY-MM-DD] people-ingest | Source Title
Processed [[source-filename.md]]. Created N new pages, updated M existing pages.
New: [[page-1]], [[page-2]].
Updated: [[page-3]] (added depth progression), [[page-4]] (new skill links).
```

### 7. Report results

Tell the user:
- Pages created (with categories)
- Pages updated (with what changed)
- Cross-links added
- Any missing information that needs additional sources

## Enrichment Operations

When asked to enrich existing pages without new sources:

### Enrich Roles with Skills

For each role page:

1. Read all competency skill files to understand depth levels
2. Add Level Differentiation section after Role Summary
3. Update competency tables to 3 columns with:
   - Skill links using `[[skill#IC Track Depth Progression|Skill Name]]` or `[[skill#M-Track Depth Progression|Skill Name]]`
   - Depth indicator matching the skill's progression table
   - Existing expectations text

### Enrich Skills with Roles

For each skill page:

1. Read all role files to understand expectations
2. Update depth progression tables with role links: `[[role-ic-1|Software Engineer]]`
3. Ensure each level has accurate depth indicator and behaviors
4. Add SDLC Application section linking to relevant steps

### Cross-link Processes

For each process/step page:

1. Identify skills applied in each step
2. Update step pages with skill links
3. Update skill pages with SDLC Application references

## Validation Checklist

Before completing ingestion, verify:

- [ ] All role pages have Level Differentiation section
- [ ] All role competency tables have 3 columns
- [ ] All skill pages have depth progression tables with role links
- [ ] All skill references in roles use section anchors
- [ ] All role references in skills use `[[role-{track}-{level}|{Level}]]` format
- [ ] Terminal levels don't reference "next" level
- [ ] M shows transition from IC track
- [ ] wiki/portal.md updated with new pages
- [ ] wiki/log.md updated with operation

## Conventions

- **Role naming**: `role-ic-{level}.md` for IC track, `role-mgmt-{level}.md` for M track
- **Skill section anchors**: `#IC Track Depth Progression` and `#M-Track Depth Progression`
- **Depth indicators**: Bold text like `**Best practices expert**`
- **Level references**: Always use full wikilink `[[role-ic-1|Software Engineer]]` not just `Software Engineer`
- **Inside tables**: Escape `|` in wikilinks: `[[role-ic-1\|Software Engineer]]` to avoid collision with table column separators
- **Prefer updates over creates**: Update existing pages when information overlaps
- **Cross-link bidirectionally**: Roles → Skills and Skills → Roles

## What's Next

After ingesting people sources:
- **Query** with `/second-brain-query` to explore career paths or skill requirements
- **Lint** with `/second-brain-lint` to check for broken links or missing cross-references
- **Ingest more** — add additional career ladder or competency sources
