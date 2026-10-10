# Interview Step Registry

Step-specific overrides for the question guide. `SKILL.md` builds the **generic** guide (step 6). When the chosen `{step}` has a file here, load **only that file** and apply its overrides.

| Step | File | Hire step | Question mode | Shape | Status |
|------|------|-----------|---------------|-------|--------|
| `engineering-screen` | [engineering-screen.md](engineering-screen.md) | 1b | Retrospective deep dives on résumé claims | ~45 min | Preliminary |
| `coding` | — | 2 | Generic guide | — | Not yet specialised |
| `system-design` | [system-design.md](system-design.md) | 3 | One live design problem | ~60 min | Active |
| `hiring-manager` / `team-match` | — | — | Generic guide | — | Not yet specialised |
| `bar-raiser` | — | — | Generic guide | — | Not yet specialised |

## Adding a step

1. Copy the section layout below into `{step}.md`. Keep it generic: no candidate names, team names or real numbers (those go in the wiki).
2. Add a row to the table above.
3. If the step has an eligibility gate (level, track), state it in the file **and** in SKILL.md Question 3.

## Step file contract

Every step file has these sections, in this order. Leave out a section only if the step doesn't change it.

| Section | Content |
|---------|---------|
| **Gate** | Who the step applies to (optional) |
| **Read first** | The wiki step page, the rubric, and the question bank to load |
| **Core rule** | The one principle that sets the step apart, plus the most common failure |
| **What changes vs the generic guide** | Table: aspect / generic / this step |
| **Question categories** | Replace or constrain the generic 5-7 categories |
| **Step-specific section** | Markdown block inserted at the guide's `{Step-specific section}` slot |
| **Interview shape** | Duration and time split |
| **Red flag to pre-load** | The failure pattern the interviewer should expect |
| **Checklist additions** | Items appended to SKILL.md's Quality Checklist |
