# Vault Map

This skill belongs to **one dedicated vault** (dedicated to interviews). The vault owns every company-specific detail: levels, step gates, durations, rubric weights, recommendation bands, assessment frameworks and challenge banks. **This file only says where to find them.** Read the details from the pages at run time and don't copy them into the skill.

All paths are relative to the vault root. Entry point: `wiki/portal.md` → *People › Roles*, *People › Steps › Hiring Process Steps*, *Resources › Artifacts › Hiring*. If a path below has moved, find it again from the portal and update this file.

## Inputs

| Resource | Path | What to pull |
|----------|------|--------------|
| Candidate raw materials | `raw/People/Candidates/{Candidate Name}/` | Résumé, briefing, LinkedIn, intake, prior feedback |
| Hiring process | `wiki/people/processes/hiring-process.md` | Step order, conditional steps, gates, recommendation thresholds |
| Step pages | `wiki/people/steps/step-hire-{n}-{name}.md` | **Applies to** (gate), **Duration**, **Rubric** link, objectives, question bank / challenge bank, red flags, next step |
| Step rubrics | `wiki/resources/artifacts/hiring/interview-rubric-{name}.md` | Criteria + weights, scoring scale, **Recommendation Bands**, level calibration, probing questions |
| Evaluation guide | `wiki/resources/artifacts/hiring/interview-evaluation-guide.md` | Score expectations by level, feedback format (Pros/Cons) |
| Assessment framework | the **5 Buckets Framework** section of `interview-rubric-bar-raiser.md` | Bucket names and what each assesses (used for the candidate page's pre-assessment) |
| Competency ladders | `wiki/people/roles/{p,m,tpm}-track-competency-ladder.md` | **Dimensions** (the leveling-table rows), level scaffolding, calibration rules |
| Role pages | `wiki/people/roles/role-{track}-{level}.md` | Level text for floor / target / stretch, "Key differentiator" vs the adjacent level |
| Competencies | `wiki/people/competencies/{competency}.md` | Wikilink targets for dimensions and skills |
| Challenge bank | `wiki/resources/components/design-*.md` (listed in each step page's *Challenge Bank*) | Reusable problems, their topics and level range |
| Team-specific interviews | `wiki/projects/product-{product}/system-interview-*.md` | Team's own challenge and rubric additions |
| Job description | `wiki/projects/product-{product}/jd-*.md`, `wiki/projects/jd-*.md` | Mission lines, must-haves, level range |
| Interview synthesis | `wiki/synthesis/{step}-{level}-{domain}.md` | Existing tailored guide for this step × level × domain |
| Prior candidates (same product) | `wiki/projects/product-{product}/_interviews_/candidate-*/` | Comparison targets, which must be wikilinked |

## Step key → vault pages

| Step key (used in file names) | Aliases (sibling interview skills) | Step page | Rubric |
|-------------------------------|------------------------------------|-----------|--------|
| `recruiter` | — | `step-hire-1-recruiter` | — |
| `engineering-screen` | — | `step-hire-1b-engineering-screen` | `interview-rubric-engineering-screen` |
| `coding` | `technical` | `step-hire-2-coding` | `interview-rubric-coding` (or `interview-rubric-ai-coding` for the AI-enabled format) |
| `system-design` | — | `step-hire-3-system` | `interview-rubric-system` |
| `team-match` | `hiring-manager`, `culture` | `step-hire-4-team-match` | `hire-4-team-match-template` |
| `bar-raiser` | — | `step-hire-5-bar-raiser` | `interview-rubric-bar-raiser` |

Step order, and which steps are conditional, come from `hiring-process.md`. If the user gives an alias, use the canonical key in file names.

## Outputs

| Output | Path |
|--------|------|
| Candidate folder | `wiki/projects/product-{product}/_interviews_/candidate-{slug}/` |
| Source page | `wiki/sources/source-{slug}.md` |
| Product page (pipeline table) | `wiki/projects/product-{product}/product-{product}.md`. If missing, use the product folder's main page |
| Portal | `wiki/portal.md`, under `#### Candidate Evaluations`. Create the section under *Projects* if it is missing |
| Log | `wiki/log.md` |
