---
name: interview-1-preparation
description: >
  Pre-interview preparation skill. Creates candidate source page with profile analysis,
  strengths/concerns assessment, and tailored interview questions. Use when the user
  says "prepare for interview", "pre-interview {name}", or wants to prep before meeting a candidate.
allowed-tools: Bash Read Write Edit Glob Grep AskUserQuestion
---

# Interview Preparation (Pre-Interview)

Create candidate evaluation materials: profile analysis, floor/target/stretch leveling, and a tailored interview guide.

This skill is generic and belongs to **one dedicated vault**. The vault owns everything company-specific: levels, step gates, durations, rubrics, bands, assessment frameworks and challenge banks. [`references/vault-map.md`](references/vault-map.md) says where each one lives. Read it first, and pull details from the vault pages; never hard-code them here.

## References (load on demand)

| File | Load when |
|------|-----------|
| [`references/vault-map.md`](references/vault-map.md) | Step 1, always |
| [`references/steps/README.md`](references/steps/README.md) → `steps/{step}.md` | Step 3b, only for the chosen step and only if its file exists |
| [`references/templates/candidate-page.md`](references/templates/candidate-page.md) | Step 5 |
| [`references/templates/question-guide.md`](references/templates/question-guide.md) | Step 6 |
| [`references/templates/source-page.md`](references/templates/source-page.md) | Step 7 |
| [`references/templates/wiki-updates.md`](references/templates/wiki-updates.md) | Steps 8–11 |
| [`references/cases/README.md`](references/cases/README.md) | Optional, before step 6: load one case only if its step and shape match |

## Input

Raw materials in the candidate folder (vault map → Inputs).

Required: résumé (PDF or Markdown).
- Experience, skills, education
Optional files:
- Interview briefing or JD — Role context, team, hiring manager
- LinkedIn profile — Current role, tenure
- Recruiting intake form — Success metrics, challenges
- Previous feedback — Prior interview rounds

## Output

- `{candidate folder}/1-candidate-{slug}.md`: candidate evaluation page
- `{candidate folder}/2-{step}-questions-{slug}.md`: interview guide
- `source-{slug}.md`, a product pipeline row, a portal entry and a log entry (vault map → Outputs)

## Workflow

### 1. Gather Context

Read `references/vault-map.md`. Then check context to get these answers (ONLY ask if not clear):

**Question 1: Product/Team**
> "Which product/team is this candidate interviewing for?"

List the product folders under the vault's projects folder as options. The user can pick one or give a new name.

**Question 2: Role and Level**
> "What role and level is this candidate interviewing for?"

Offer the level codes from the vault's role pages / competency ladders (e.g. "{Title} ({level code})"). If the recruiter suggested a level, or the JD gives a range, note it. Step 3b turns this into floor / target / stretch.

**Question 3: Interview Step**
> "Which interview step are you preparing for?"

Options are the steps in the vault's hiring process after the recruiter screen, using the step keys in the vault map. For a conditional step, read the step page's **Applies to** line and offer it only if the target level passes.

**Question 4: Focus Areas (Optional)**

Check prior feedback for identified concerns or strengths, ONLY in case of doubt ask :

> "Any specific areas you want to probe? Leave blank for standard assessment."

### 2. Read Raw Materials

For each file in the candidate folder:

| File Type | What to Extract |
|-----------|-----------------|
| **Résumé** (PDF/Markdown) | Experience timeline, skills, education, accomplishments with metrics, verbatim summary line |
| **Briefing** | Role context, hiring manager, team structure, interview panel |
| **LinkedIn** | Current role, tenure, career trajectory |
| **Intake form** | Success metrics, challenges, interview focus areas |
| **Prior feedback** | Scores, interviewer, verbatim concerns and strengths |

### 3. Read the Vault Pages for This Round

Using the vault map, read **only** what this round needs:

- Step page and step rubric for `{step}`: duration, question/challenge bank, red flags, criteria + weights, recommendation bands, level calibration
- The track's competency ladder (its dimensions become the leveling rows) and the role pages for floor, target and stretch
- The assessment framework, for the candidate page's pre-assessment
- The JD and any team-specific interview page for the product
- An existing interview synthesis for this step × level × domain, if one exists
- Prior candidates in the same product: any comparison ("same gap as X") **must be a wikilink** to that candidate's page, never a bare first name

### 3b. Decide the Round's Load (before writing anything)

Write down, for yourself, these four answers. Every section of both output files must serve them:

1. **Floor / target / stretch level**: target = recruiter-suggested level (else Question 2; if only a range is given, its upper bound). Floor and stretch are the adjacent levels on the vault's ladder, one below and one above. Include intermediate tiers such as a "-II" level if the ladder has them.
2. **The single highest-priority probe**: usually the recruiter's or prior interviewer's named concern. Quote it verbatim.
3. **The candidate's strongest asset** for this role (the JD/mission line it maps to).
4. **What is NOT this round's job**: concerns to route to a later step (name the step).

Then load `references/steps/{step}.md` if it exists (see the registry). It says how this step uses the four answers, overrides parts of the generic guide, and adds checklist items.

### 4. Create Output Directory

```bash
mkdir -p {candidate folder}
```

### 5. Create Candidate Evaluation Page

Fill `references/templates/candidate-page.md`.

### 6. Create Interview Questions Guide

Fill `references/templates/question-guide.md`, applying the step file's overrides if there is one.

### 7. Create Source Page

Fill `references/templates/source-page.md`.

### 8–10. Update Product Page, Portal, Log

Use the snippets in `references/templates/wiki-updates.md`.

### 11. Report Results

Use the report block in `references/templates/wiki-updates.md`.

### 12. Stage Changes

Call `/change-management-1-stage`:

```
/change-management-1-stage
  trigger: {user's original instruction}
  operation: pre-interview
  subject: {Candidate Name}
  input_files: {all raw files in candidate folder}
  created_files: {all pages created}
  updated_files: {product page, portal, log}
```

Do not commit unless the user explicitly asks.

## Quality Checklist (run before writing each file)

Fix any "no" before saving:

- [ ] Background quote is **verbatim** from the résumé; interpretation lives outside the quote.
- [ ] Every claim is traceable to the source files (no inferred skills, no invented numbers).
- [ ] Level codes, dimensions, buckets, durations, weights and bands come from vault pages, not memory.
- [ ] Leveling uses **floor / target / stretch**; tags carry the target only.
- [ ] Exactly **one** concern is marked as the central/highest-priority probe, with a verbatim quote of its source.
- [ ] Concerns this round can't resolve are routed to a named later step.
- [ ] Other candidates are referenced by **wikilink**, never bare names.
- [ ] Quoted questions contain **no internal names or notes** (recruiter, interviewer, other candidates, "your file says"): they are spoken to the candidate.
- [ ] Each question has *Listening for:* **and** *{Target} signal:*.
- [ ] Questions numbered Q1…Qn continuously; flow/red-flag/signal tables cite Q numbers.
- [ ] Flow time ranges end exactly at the round duration; backups listed.
- [ ] Recommendation gives **conditional outcomes**, never a predicted verdict.
- [ ] Table cells ≤ ~25 words; reasoning goes in prose below the table.
- [ ] The step file's *Checklist additions* (if any) all pass.

## Conventions

- **Slug format:** lowercase, hyphenated name (e.g. `jane-d`)
- **File numbering:** `1-` for candidate page, `2-` for questions guide
- **Step keys in file names:** as listed in the vault map
- **Leveling:** always floor / target / stretch, using the vault ladder's level codes
- **Questions:** 25-35 tailored questions across 5-7 categories, unless the step file says otherwise
- **Evidence tables:** always include specific examples from source materials
- **Pre-assessment:** mark each bucket Strong/Probe/Gap with a priority
- **Red flags/signals:** 5-8 specific, observable patterns, each citing Q numbers
- **Tone:** decisive and prioritized: bold the one thing that matters most in each section; concise over exhaustive

## Edge Cases

**Missing briefing:** focus on the résumé; ask the user for role context.

**No product specified:** ask the user; it's needed for the output location.

**Prior feedback exists:** extract scores, concerns and strengths, and build on them.

**Level range given (e.g. JD says "{level A} or {level B}"):** target = recruiter-suggested level if any, else the upper bound; still bracket floor and stretch.

**Vault page missing** (no rubric, no ladder, no step page): say which one is missing, ask the user, and don't fill the gap from general knowledge.

**Synthesis doesn't exist:** offer to create a role-specific interview guide first.
