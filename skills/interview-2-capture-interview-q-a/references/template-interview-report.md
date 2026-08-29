# Template: Interview Report Note

Copy this template to `wiki/projects/product-{product}/_interviews_/candidate-{slug}/{n}-{step}-report-{slug}.md` and fill in placeholders.

Use this to **capture an AI-generated (or interviewer-written) interview report** — a condensed, section-based synthesis of how a candidate performed in one interview. It is the *summary* layer: it distills the interview into themed prose and a Pros/Cons read, without scoring or a hire decision. Produce it from a AI report, an AI recruiting summary, or your own post-interview notes.

## What this is — and is NOT

| | Interview Report (this template) | [[template-interview-q-a\|Q&A Note]] | Candidate Evaluation |
|---|---|---|---|
| **Answers** | *"How did they do, in summary?"* | *"What was asked and what did they say?"* | *"How good was it, and do we hire?"* |
| **Granularity** | Condensed themes + Pros/Cons | Question-by-question, faithful | Scored competencies + verdict |
| **Voice** | Synthesized read, light judgment | Neutral capture | Judgment — scores, level, recommendation |
| **Source** | AI report / interviewer synthesis | Transcript / AI Q&A summary | Report + Q&A note combined |
| **Grows into** | Feeds the evaluation | Feeds the evaluation | Feeds the hiring decision |

The report *summarizes*; the Q&A note *records*; the evaluation *decides*. A short screen may produce only a report. A deep round should have both a Q&A note (fidelity) and a report (gist) before the evaluation scores them.

## Design principle: themed synthesis, Pros before Cons, evidence-grounded

- **Themed synthesis** — each section is a short paragraph (or tight bullets) answering one question about the candidate: *what can they do?*, *how do they decide?*, *why are they here?*. Prose over transcript.
- **Pros before Cons** — lead the technical read with what they demonstrated, then what wobbled. Keep both concrete: "needed prompting to identify crawler-loop risks" beats "some gaps."
- **Evidence-grounded, judgment-light** — name the specific thing they did (the mechanism, the number, the trade-off they weighed), not a rating. Scores and the hire call belong in the evaluation, not here. A report can *lean* ("wobbled on point-in-time skew") but must not *verdict* ("3/5, no hire").
- **Preserve the wobble** — hedges, "needed prompting," "was unsure," and self-corrections are the highest-value signal. Never smooth them into competence the candidate didn't show.

---

## The template

```markdown
---
Category: projects
Tags: [hiring, interview-report, candidate, {slug}, {product}, {level}, {step}]
Source links:
  - [[source-{slug}]]
  - [[1-candidate-{slug}]]
Created: {YYYY-MM-DD}
Last Updated: {YYYY-MM-DD}
---

# Interview Report: {Full Name}

**Role:** {Title} ({Level})
**Team:** {Product}
**Interview Step:** [[step-hire-{n}-{step}|{Step Name}]]
**Interviewer:** {Name}
**Date:** {YYYY-MM-DD}
**Source:** {AI summary / interviewer notes}

## TL;DR

{2-4 sentences: the shape of the interview and the headline read — what they showed, what wobbled. No scores.}

## Technical Abilities

### Pros
- {Concrete thing they demonstrated — a design, a mechanism, a trade-off they named}
- {Another concrete strength, with the specifics}
- {Another}

### Cons
- {A concrete gap — "was unsure how X relates to Y", "needed prompting to identify Z"}
- {Another gap, specific}
- {Another}

## Summary

{One paragraph: the overall arc of the interview. What they communicated about their experience, how they approached the problem(s), where they were fluent and where they needed help. Neutral-to-light judgment — describe, don't score.}

## Critical Decision Making

{One paragraph: the reasoning they showed on the core problem. The trade-offs they weighed (cost vs freshness, batch vs real-time, consistency vs latency), the criteria they used to decide, and where the reasoning held or broke. This is the depth read — be specific about the *mechanism* of their thinking.}

## Motivation

{One paragraph: why they're looking, what they're seeking, and how they reacted to this role. Capture their own framing — "wants intellectually stimulating work", "dislikes bureaucracy", "excited to wear many hats". Motivation is a seniority and retention signal; record it faithfully.}

## AI Mindset

- {What AI/ML-adjacent work they've actually done — feature generation, MLOps, serving models, etc.}
- {How they think about AI in the workflow}
- {Whether they use AI tools to work faster — and if this wasn't discussed, say so explicitly}

## Notable Quotes

> "{Direct quote worth preserving — a crisp trade-off, a red flag, a strong ownership statement.}"

## Open Threads / Not Covered

- {Planned topic that time ran out on — flag for a later round}
- {Ambiguous read that needs follow-up before a decision}

## Related

- [[1-candidate-{slug}|Candidate Evaluation (Pre-Interview)]]
- [[{n}-qa-{slug}|Interview Q&A Note]] — the faithful capture this summarizes
- [[{n}-evaluation-{slug}|Post-Interview Evaluation]] — scores this report feeds
- [[source-{slug}|Source Profile]]
- [[interviews-{product}|{Product} Hiring]]
```

---

## How to fill it correctly

Apply editorial judgment first — a short screen may only need Pros/Cons and a Summary. Then follow the per-section rules.

### Frontmatter
- **`Tags`** — always lead with `hiring, interview-report`; then `candidate`, the `{slug}`, `{product}`, `{level}`, `{step}`. This keeps the report findable next to the candidate's other pages.
- **`Source links`** — link the source profile and the pre-interview candidate page so the report sits in the candidate's dossier. Leave a link plain text if the target page doesn't exist yet (check wiki-schema).
- **`Last Updated`** — bump whenever you revise the read (e.g., after a second pass or reconciling with the Q&A note).

### Header block
State **Interviewer**, **Date**, and **Source** explicitly. The source matters most here: an AI report is *already* a synthesis and may have dropped hedges or over-smoothed — note it so a reader knows the read is second-hand. If you wrote it from your own notes, say so.

### TL;DR
*Write this last.* 2-4 sentences on the *shape* of the interview and the headline read. Describe, don't score — "fluent on feature-path design, wobbled on point-in-time skew and needed prompting on crawler loops" not "3/5 on system design." If you can't summarize without inventing a verdict, you're drifting into the evaluation.

### Technical Abilities (Pros / Cons)
The spine of the report. Rules:
- **Pros first, then Cons** — lead with what they demonstrated.
- **One concrete point per bullet.** Name the specific design, mechanism, or trade-off: "Designed batch and near-real-time paths using Kafka, DynamoDB, S3, Databricks" — not "good system design."
- **Cons are behaviors, not labels.** "Was unsure how point-in-time data and skew relate", "needed prompting to identify crawler parsing and loop concerns" — these tell the evaluation *exactly* what to probe next. Avoid vague cons like "some gaps in depth."
- **3-5 bullets per side** is typical; fewer for a short screen.

### Summary
One paragraph on the arc of the interview: what experience they communicated, how they approached the problem, where they were fluent, where they needed help. This is the "read it in one pass" section — light judgment is fine, scores are not.

### Critical Decision Making
The depth read. One paragraph on the *reasoning* they showed: the trade-offs they weighed and the criteria they used to decide. Be specific about mechanism — "routed short-window lookups (1-7 days) to DynamoDB GSIs with a 1,000-row limit, and assigned year-long joins to daily batch, weighing batch cost against freshness." This is where you show whether their decisions were principled or improvised.

### Motivation
One paragraph capturing *their own framing* of why they're looking and what they want. This is a seniority and retention signal — record it faithfully, including tells like "dislikes bureaucracy" or "current project reaching maturity / maintenance mode." Note how they reacted to *this* role specifically.

### AI Mindset
Increasingly a required read. Bullets covering: (1) what AI/ML-adjacent work they've actually done, (2) how they reason about AI in the workflow, (3) whether they use AI tools to work faster. **If a dimension wasn't discussed, say so explicitly** ("No use of AI tools to work faster was discussed") — the absence is itself signal, and prevents the evaluation from over-claiming.

### Notable Quotes
Pull 1-5 verbatim lines worth preserving — a crisp trade-off, a revealing red flag, a strong statement. These are the evidence the evaluation will cite. Skip if the source is a paraphrased AI report with no verbatim lines.

### Open Threads / Not Covered
Honesty section. List planned topics time cut off, and reads too ambiguous to act on. This tells the next interviewer what to probe and stops the evaluation from over-claiming coverage.

### Related
Link the pre-interview candidate page, the Q&A note this report summarizes (if one exists), the post-interview evaluation this report feeds, the source profile, and the team hiring page. Resolve links against the existing wiki (per the vault CLAUDE.md) before adding them; unresolved names stay plain text.

---

## Conventions

- **Synthesis over transcript.** This is the gist layer — if you find yourself recording every question verbatim, you want the [[template-interview-q-a|Q&A Note]] instead.
- **Pros before Cons, always.** Lead with capability, then gaps.
- **Cons are actionable, not vague.** Name the specific wobble so the evaluation knows what to probe.
- **Preserve the wobble.** "Needed prompting", "was unsure", "did not recall exactly" are gold — never edit them out to make the read cleaner.
- **Light judgment, no verdict.** A report can lean; it must not score or make the hire call. That belongs in [[template-candidate-evaluation|the evaluation]].
- **One report per interview step.** A candidate with coding + system-design + team-match rounds gets three reports, each linked from the candidate page.
- **Note the source's bias.** AI reports are pre-condensed; flag them so a reader knows the capture is second-hand.

---

## Minimal Interview Report

For a short screen or single-topic round — drop the Motivation, AI Mindset, and Notable Quotes sections. Keep the header, Pros/Cons, a Summary, and open threads.

```markdown
---
Category: projects
Tags: [hiring, interview-report, candidate, {slug}, {product}, {step}]
Source links:
  - [[source-{slug}]]
Created: {YYYY-MM-DD}
Last Updated: {YYYY-MM-DD}
---

# Interview Report: {Full Name}

**Step:** {Step} · **Interviewer:** {Name} · **Date:** {YYYY-MM-DD} · **Source:** {notes}

## TL;DR

{2-3 sentences, neutral-to-light judgment.}

## Technical Abilities

### Pros
- {Concrete strength}
- {Concrete strength}

### Cons
- {Concrete gap}
- {Concrete gap}

## Summary

{One paragraph on the arc of the interview.}

## Open Threads

- {What wasn't covered / needs follow-up}

## Related

- [[source-{slug}|Source Profile]]
- [[interviews-{product}|{Product} Hiring]]
```
