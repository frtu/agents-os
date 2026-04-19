# People Wiki Schema

Canonical rules for maintaining the `wiki/people/` knowledge base structure. This schema governs career ladders, competencies, processes, and team organization.

## Architecture

The `wiki/people/` directory contains all content related to team members, their skills, and organizational processes.

### Directory Structure

```
wiki/people/
├── competencies/     # Skills and abilities
│   ├── {category}.md        # Category pages (craft, culture, leadership, talent, result)
│   └── {skill-name}.md      # Individual skill pages
├── roles/            # Career ladder roles
│   ├── engineering-career-ladder.md   # Overview page
│   ├── role-ic-{level}.md             # IC track: role-ic-1.md
│   └── role-mgmt-{level}.md           # M track: role-mgmt-1.md
├── processes/        # Multi-step workflows
│   └── {process-name}.md    # e.g., software-development-lifecycle.md
├── steps/            # Individual process steps
│   └── step-{name}.md       # e.g., step-planning.md, step-design.md
└── members/          # Individual team members
    └── {name}.md            # e.g., fred.md
```

### Raw Source Locations

People-related raw sources are typically found in:

- `raw/notes/people/` — career ladder docs, competency frameworks, process definitions
- `raw/notes/people/processes/` — SDLC, operating principles, frameworks
- `raw/notes/people/steps/` — process step definitions
- `raw/notes/people/competencies/` — skill definitions, progression frameworks
- `raw/notes/people/roles/` — career ladder roles with levels and tracks (e.g., role-ic-1)
- `raw/notes/people/members/` — individual role descriptions, career ladder levels

## Page Formats

### Competency Category Pages

Category pages group related skills and provide overview context.

**Filename:** `{category}.md` (e.g., `craft.md`, `leadership.md`)

```markdown
---
Category: people/competencies
Tags:
  - competency-category
  - {category-name}
Source links:
  - source-file.md
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
---

# {Category Name}

Brief description of what this competency category covers.

## Skills in This Category

| Skill | Track | Description |
|-------|-------|-------------|
| [[skill-name\|Skill Name]] | IC + M | Brief description |
| ... | ... | ... |

## Category Overview

How these skills relate to each other and overall career progression.

## Related

- [[other-category]] — relationship context
```

### Individual Skill Pages

Skill pages document specific competencies with depth progression by level.

**Filename:** `{skill-name}.md` (e.g., `coding-expertise.md`, `decision-making.md`)

```markdown
---
Category: {Category}
Tags: [skill, {category}, competency, {specific-tags}]
Sources:
  - source-file.md
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
---

# {Skill Name}

**Category:** [[{category}|{Category Name}]]
**Track:** IC + M | IC only | M only
**Definition:** One-sentence definition of the skill.

## Measurement Indicators

| Dimension | Junior | Mid | Senior |
|-----------|--------|-----|--------|
| **Metric 1** | Expected | Expected | Expected |
| ... | ... | ... | ... |

## Red Flags

- Warning sign 1
- Warning sign 2

## Growth Actions

| From | To | Actions |
|------|----|---------|
| 1 | 2 | Growth actions |

## SDLC Application

Which [[software-development-lifecycle|SDLC]] steps most apply this skill:

- [[step-{name}|Step Name]] — how this skill applies
```

### Role Pages (Career Ladder)

Role pages define expectations for each level in IC or M track.

**IC Track Filename:** `role-ic-{level}.md` (e.g., `role-ic-1.md`, `role-ic-3.md`)
**M Track Filename:** `role-mgmt-{level}.md` (e.g., `role-mgmt-1.md`, `role-mgmt-3.md`)

```markdown
---
Category: people/roles
Tags:
  - career-ladder
  - individual-contributor | management
  - {track}-track
  - {level-tag}
Source links:
  - source-file.md
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
---

# {Level} — {Title}

> *Persona quote describing the role's essence*

## Role Summary

| Attribute | Value |
|-----------|-------|
| **Level** | {Level} |
| **Title** | {Title} |
| **Scope** | {Scope} |
| **Craft Time** | {Percentage range} |

Brief paragraph describing the role.

## Level Differentiation

**What makes {Level} distinct from other levels:**

| Compared To | {Level} Difference |
|-------------|-------------------|
| ← [[role-{track}-{prev}\|{Prev}]] | {Prev} does X; {Level} does **Y** |
| → [[role-{track}-{next}\|{Next}]] | {Level} does Y; {Next} does **Z** |

**{Level} Focus Areas:**
- **Focus 1**: Description
- **Focus 2**: Description
- ...

**Key {Prev} → {Level} Transitions (achieved):**
1. **Competency**: "Previous expectation" → "current expectation"
2. ...

**Key {Level} → {Next} Transitions (next):**
1. **Competency**: "Current expectation" → "next expectation"
2. ...

## Competency Expectations

### [[{category}|{Category Name}]]

| Competency | Depth | Expectations |
|------------|-------|--------------|
| [[{skill}#{Track} Track Depth Progression\|{Skill Name}]] | **Depth indicator** | Detailed expectations |
| ... | ... | ... |

(Repeat for each category: Craft, Culture, Leadership, Talent, Result)

## What Good Looks Like

- Observable behavior 1
- Observable behavior 2
- ...

## Growth Path

**Previous Level: [[role-{track}-{prev}|{Prev} — {Title}]]**

**Next Level: [[role-{track}-{next}|{Next} — {Title}]]**

Key transitions:
- From X → Y
- ...

## Related

- [[engineering-career-ladder|Engineering Career Ladder]] — Full ladder context
- [[{skill}|{Skill}]] — Key competency at this level
```

### Career Ladder Overview Page

**Filename:** `engineering-career-ladder.md`

```markdown
---
Category: people/roles
Tags:
  - career-ladder
  - overview
Source links:
  - source-files
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
---

# Engineering Career Ladder

Overview of the dual-track career system.

## Track Overview

| Track | Levels | Focus |
|-------|--------|-------|
| IC (Individual Contributor) | 1-7 | Technical depth |
| M (Management) | 1-5 | People leadership |

## Competency Categories

| Category | Description |
|----------|-------------|
| [[craft\|Craft]] | Technical skills |
| [[culture\|Culture]] | Collaboration and communication |
| [[leadership\|Leadership]] | Decision making and strategy |
| [[talent\|Talent]] | Hiring and coaching |
| [[result\|Result]] | Impact and ownership |

## Related

- Competency pages
- Process pages
```

### Process Pages

**Filename:** `{process-name}.md` (e.g., `software-development-lifecycle.md`)

```markdown
---
Category: people/processes
Tags:
  - process
  - {relevant-tags}
Source links:
  - source-file.md
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
---

# {Process Name}

Overview description.

## Steps

| Step | Description | Key Skills |
|------|-------------|------------|
| [[step-{name}\|{Name}]] | Brief description | [[skill1]], [[skill2]] |
| ... | ... | ... |

## Process Flow

(Diagram or description of how steps connect)

## Related

- [[related-process]] — context
```

### Step Pages

**Filename:** `step-{name}.md` (e.g., `step-planning.md`, `step-design.md`)

```markdown
---
Category: people/steps
Tags:
  - step
  - sdlc
  - {specific-tags}
Source links:
  - source-file.md
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
---

# {Step Name}

Brief description of this step.

## Overview

What this step accomplishes and when it occurs.

## Key Activities

- Activity 1
- Activity 2

## Skills Applied

| Skill | Application |
|-------|-------------|
| [[skill-name\|Skill Name]] | How this skill applies |
| ... | ... |

## Inputs & Outputs

| Inputs | Outputs |
|--------|---------|
| Input 1 | Output 1 |
| ... | ... |

## Related

- [[{process}|Process]] — parent process
- [[step-{prev}\|Previous Step]] — what comes before
- [[step-{next}\|Next Step]] — what comes after
```

## Cross-Linking Rules

### Role → Skill Links

In role pages, link to skill pages with section anchors for track-specific depth:

```markdown
[[{skill}#IC Track Depth Progression\|{Skill Name}]]
[[{skill}#M-Track Depth Progression\|{Skill Name}]]
```

### Skill → Role Links

In skill pages, link to role pages in the depth progression tables:

```markdown
[[role-ic-1\|Software Engineer]]
[[role-mgmt-1\|Team Lead]]
```

### Process → Step → Skill Links

- Process pages link to all their steps
- Step pages link to skills applied in that step
- Skill pages link back to steps where they're applied (in SDLC Application section)

### Category → Skill Links

- Category pages list all skills in that category
- Skill pages link back to their category

## Naming Conventions

| Content Type | Filename Pattern | Title Pattern |
|--------------|------------------|---------------|
| Category | `{category}.md` | `# {Category Name}` |
| Skill | `{skill-name}.md` | `# {Skill Name}` |
| IC Role | `role-ic-{level}.md` | `# {Level} — {Title}` |
| M Role | `role-mgmt-{level}.md` | `# {Level} — {Title}` |
| Process | `{process-name}.md` | `# {Process Name}` |
| Step | `step-{name}.md` | `# {Step Name}` |
| Member | `{name}.md` | `# {Name}` |

## Enrichment Patterns

When enriching role files:

1. **Add Level Differentiation section** after Role Summary
   - Comparison table with ← previous and → next levels
   - Focus areas for this level
   - Key transitions achieved (from previous level)
   - Key transitions next (to next level)

2. **Update competency tables** to 3 columns
   - Competency (with section anchor link)
   - Depth (bold indicator)
   - Expectations (detailed text)

When enriching skill files:

1. **Add depth progression tables** for both IC and M tracks
2. **Include measurement indicators** with Junior/Mid/Senior progression
3. **Add red flags** section for warning signs
4. **Add growth actions** table for level transitions
5. **Add SDLC Application** section linking to relevant steps

## Validation Rules

1. Every role page must have a Level Differentiation section
2. Every role page competency table must have 3 columns (Competency, Depth, Expectations)
3. Every skill page must have IC Track and/or M-Track Depth Progression sections
4. All role references in skill pages must use `[[role-{track}-{level}|{Level}]]` format
5. All skill references in role pages must include section anchors
6. Terminal levels should not have "→ next" comparison
7. Entry levels should show transition from IC track for M track
