# Interview Step Registry

Step-specific overrides for the question guide. SKILL.md builds the **generic** guide from `templates/question-guide.md`. When the chosen `{step}` has a file here, load **only that file** and apply its overrides.

The step key → vault step page / rubric mapping is in [vault-map.md](../vault-map.md). Gates, durations and rubric details are read from those pages, not from here.

| Step key | File | Question mode | Status |
|----------|------|---------------|--------|
| `engineering-screen` | [engineering-screen.md](engineering-screen.md) | Retrospective deep dives on résumé claims + gap routing | Active |
| `coding` | — | Generic guide | Not yet specialised |
| `system-design` | [system-design.md](system-design.md) | One live design problem | Active |
| `team-match` | — | Generic guide | Not yet specialised |
| `bar-raiser` | — | Generic guide | Not yet specialised |

## Adding a step

1. Write `{step-key}.md` with the sections below. Keep it generic: no candidate names, and no gates, durations, weights or bands copied from the vault. Point to the step page and rubric instead.
2. Add a row to the table above, and to the vault map's step table if the key is new.

## Step file contract

Every step file has these sections, in this order. Leave out a section only if the step doesn't change it.

| Section | Content |
|---------|---------|
| **Gate** | Only for conditional steps: "check the step page's *Applies to*" |
| **Read first** | Which parts of the step page, the rubric and the challenge/question bank to read |
| **Core rule** | The one principle that sets the step apart, plus the most common failure |
| **What changes vs the generic guide** | Table: aspect / generic / this step |
| **Question categories** | Replace or constrain the generic 5-7 categories |
| **Step-specific section** | Markdown block inserted at the guide's `{Step-specific section}` slot |
| **Red flag to pre-load** | The failure pattern the interviewer should expect |
| **Checklist additions** | Items appended to SKILL.md's Quality Checklist |
