	# Evaluation Template

Post-interview evaluation page template.

**Two-tier structure:**
- **TOP (Decision Section)** — Tight, decision-focused. Coarse grain Pros/cons, level calibration, limitations, verdict.
- **BOTTOM (Evidence Section)** — Thorough. SWOT, detailed interview questions, competency matrix, raw observations.

All sections required — use "Not evaluated" for aspects not probed.

## Competency Reference

Based on [[competency-matrix|Competency Matrix]]:

| Category       | Competencies                                                                | Interview Signals                               |
| -------------- | --------------------------------------------------------------------------- | ----------------------------------------------- |
| **Craft**      | Coding, Software Design, System Design, Domain Expertise, Product Expertise | Tech depth, architecture, problem decomposition |
| **Culture**    | Collaboration, Communication, Fit & Growth, Community                       | Clarity, teamwork, passion, learning            |
| **Leadership** | Decision Making, Strategy                                                   | Trade-offs, prioritization, planning            |
| **Talent**     | Hiring, Inspire                                                             | Mentoring, role modeling, team building         |
| **Result**     | Impact, Ownership, Operational Excellence                                   | Delivery, reliability, metrics-driven           |

---

```markdown
---
Category: projects
Tags: [hiring, candidate, evaluation, {step}, {level}, {domain}]
Source links:
  - [[source-{candidate-slug}]]
Created: {date}
Last Updated: {date}
---

# Candidate Evaluation: {Candidate Name}

**Role:** {Full Role Title} ({Level})
**Team:** [[{Team or JD}]] / {Location}
**Interview Step:** [[step-hire-{n}-{step}|{Step Name}]] (completed)
**Status:** Post-Interview Evaluation
**Interview Guide:** [[{synthesis-page}|{Guide Title}]]
**Interviewer:** {Interviewer Name}
**Duration:** ~{N} minutes

---

# 🎯 DECISION SECTION

## Verdict

### **{Lean Yes for Level 3 / Yes / Not yet for Level 4 / No}** ({X.X}/5)

{One decisive sentence with explicit recommendation, including level adjustment if applicable}

*{Italicized context note about evaluation limits — e.g., "Limited evaluation — only 20 min effective of 45 min scheduled"}*

---

## Level Calibration

| Field | Value |
|-------|-------|
| **Target Level** | {Level 2/Level 3/Level 4/Level 5} |
| **Demonstrated Level** | {Level 2/Level 3/Level 4/Level 5 or "Inconclusive"} |
| **Recommendation** | {Hire at target / Downlevel to Level 3 / Re-interview for Level 4 / Decline} |
| **Evaluation Confidence** | {Low / Medium / High} |

---

## Pros & Cons (Restricted)

### Pros (max 3-4)

- **{Competency}** ({X.X}/5) : {One-line evidence from interview}
- **{Competency}** ({X.X}/5) : {One-line evidence from interview}
- **{Competency}** ({X.X}/5) : {One-line evidence from interview}

### Cons (max 3-4)

- **{Competency / Gap}** ({X.X}/5) : {One-line gap or concern}
- **{Level} gap** : {Specific behavior preventing target level — e.g., "Jumps to conclusion too fast, lacks clarifications"}

### Not Evaluated

- **{Competency}** : Not evaluated — {reason: time constraints / interview scope / tangent}

---

## Depth vs Breadth

- **++ Depth** : {What they know deeply — domain, concepts, patterns}
- **-- Breadth** : {What they don't know broadly — missing areas like AI, recent tech, cross-domain}
- **Extra Miles** : {Going beyond minimum — proactive hardening, improvement proposals, curiosity}

---

## Executive Summary

| Dimension | Score | Verdict |
|-----------|-------|---------|
| **Overall Recommendation** | {X.X}/5 | **{Strong Yes/Yes/Lean Yes/No}** |
| Craft | {X.X}/5 | {Brief verdict or "Not evaluated"} |
| Culture | {X.X}/5 | {Brief verdict or "Not evaluated"} |
| Leadership | {X.X}/5 | {Brief verdict or "Not evaluated"} |
| Result | {X.X}/5 | {Brief verdict or "Not evaluated"} |

**{Level} Bar:** {✅/⚠️/❌} {Exceeds/Meets/Below/Partial} ({score} vs {threshold} minimum)

---

## Communication Breakdown

Communication is multi-dimensional — distinguish team-fit risk from content clarity.

| Category | Score | Notes |
|----------|-------|-------|
| **Technical Clarity** | {X.X}/5 | {Concept articulation regardless of medium} |
| **Structuring** | {X.X}/5 | {Anchor scope before diving in — P4 signal} |
| **Communication** | {X.X}/5 | {Communication with team, partners, leaders, remote team} |

---

## Interview Context / Limitations

| Aspect | Status |
|--------|--------|
| **Confidence in Verdict** | {Low / Medium / High} |
| **Misc Issues** | {Audio cuts / mic quality / latency / Come late / none} |
| **Unable to Assess** | {List areas that couldn't be probed and why} |

---

# 📊 EVIDENCE SECTION

## SWOT Analysis

### Strengths
- {Strength with specific evidence}
- {Strength with specific evidence}

### Weaknesses
- {Weakness with specific evidence}
- {Weakness with specific evidence}

### Opportunities (for the candidate / role fit)
- {Growth area or role match opportunity}
- {Where their experience plugs into team needs}

### Threats (risks if hired)
- {Risk to candidate success in this role}
- {Risk to team if hired}

---

## Detailed Pros & Cons (Raw)

### Pros 👍 (full observations)

1. **{Pro with specific evidence}** — {Verdict & detailed evidence with metrics/quotes}
2. **{Pro}** — {Explanation and reasoning}
3. ...

### Cons 👎 (full observations)

1. **{Con}** — {Detailed concern with context}
2. **{Con}** — {Gap identified}
3. ...

---

## Interview Questions Asked

### {Section Name — e.g., Project Deep Dive}

| Question | Response Summary | Assessment |
|----------|------------------|------------|
| "{Question asked}" | {Brief summary of answer} | {✅/⚠️/❌} **{Strong/Adequate/Weak}** — {reason} |
...

{Repeat for each section of interview}

### Questions Not Asked

| Question | Reason | Impact |
|----------|--------|--------|
| "{Planned question}" | {Why not asked} | {What we missed} |
...

---

## Competency Score Matrix (Pre vs Post)

| Competency | Pre-Score | Post-Score | Notes |
|------------|-----------|------------|-------|
| [[coding\|Coding]] | {Pre} | **{Post}** or **N/E** | {Change reason or "Not evaluated"} |
| [[software-design\|Software Design]] | {Pre} | **{Post}** or **N/E** | {Notes} |
| [[system-design\|System Design]] | {Pre} | **{Post}** or **N/E** | {Notes} |
| [[domain-expertise\|Domain Expertise]] | {Pre} | **{Post}** or **N/E** | {Notes} |
| [[communication\|Communication]] | {Pre} | **{Post}** or **N/E** | {Notes} |
| [[collaboration\|Collaboration]] | {Pre} | **{Post}** or **N/E** | {Notes} |
| [[decision-making\|Decision Making]] | {Pre} | **{Post}** or **N/E** | {Notes} |
| [[strategy\|Strategy]] | {Pre} | **{Post}** or **N/E** | {Notes} |
| [[ownership\|Ownership]] | {Pre} | **{Post}** or **N/E** | {Notes} |
| [[operational-excellence\|Operational Excellence]] | {Pre} | **{Post}** or **N/E** | {Notes} |
| [[inspire\|Inspire]] | {Pre} | **{Post}** or **N/E** | {Notes} |

---

## {Target Level} Maturity Checklist

Explicit signals for the target level — calibrates promotion vs downlevel.

| {Px} Signal | Status | Evidence |
|-------------|--------|----------|
| {Signal — e.g., "Clarifies scope before diving"} | {✅/❌/N/E} | {Evidence or "Not evaluated"} |
| {Signal — e.g., "Owns domain strategy"} | {✅/❌/N/E} | {Evidence} |
| {Signal — e.g., "Mature decision making"} | {✅/❌/N/E} | {Evidence} |
| {Signal — e.g., "Cross-boundary articulation"} | {✅/❌/N/E} | {Evidence} |
| {Signal — e.g., "Multiplier effect on team"} | {✅/❌/N/E} | {Evidence} |

---

## Evidence Details (Direct Quotes)

### Strong Signals ✅

| Competency | Evidence | Quote/Context |
|------------|----------|---------------|
| **{Competency}** | {What they demonstrated} | *"{Direct quote from transcript}"* |
...

### Weak Signals ❌

| Competency | Expected | Actual | Notes |
|------------|----------|--------|-------|
| **{Competency}** | {What we looked for} | {What we observed} | {Context} |
...

### Not Probed

| Competency | Planned Question | Status |
|------------|------------------|--------|
| {Competency} | "{Planned question}" | **Not evaluated** — {reason} |
...

---

## Interviewer Observations (Free-form)

Narrative observations that don't fit competency boxes — gut feel, qualitative signals.

> {Interviewer quote or observation}

- {Free-form note}
- {Free-form note}

**Candidate response to feedback:** {How they received any direct feedback}

---

## Recommendation Detail

### Remaining Risks

1. **{Risk}** — {Recommendation for follow-up or mitigation}
2. **{Risk}** — {Mitigation approach}

### Suggested Next Steps

- [x] Complete {Step} interview
- [ ] Share evaluation with hiring manager ({Name})
- [ ] {Follow-up for unevaluated areas}
- [ ] {Next action — e.g., "Propose Level 3 offer with re-interview for Level 4 in 12 months"}

---

## Related

- [[source-{candidate-slug}|{Name} Profile]] — Source documents
- [[{synthesis-page}|{Guide Title}]] — Interview guide
- [[role-{track}-{level}|{Level} {Title}]] — Target level definition
- [[{team-project}|{Team Name}]] — Team overview
```

---

## Usage Notes

### Two-Tier Philosophy

**TOP (Decision Section)** is what a hiring manager reads in 60 seconds:
- Verdict (with explicit level recommendation)
- Restricted pros/cons (max 3-4)
- Level calibration table
- Depth vs Breadth + Extra Miles
- Communication breakdown (multi-dimensional)
- Interview limitations and confidence

**BOTTOM (Evidence Section)** is what hiring committees and skeptics dig into:
- SWOT (4 quadrants)
- Detailed raw pros/cons (unbounded list)
- Full interview questions table (asked AND not asked)
- Competency score matrix (pre vs post, all dimensions)
- Px maturity checklist (target level signals)
- Direct quotes and evidence
- Free-form interviewer observations

### Pros & Cons (Restricted) Guidelines

1. **Max 3-4 items each** in the TOP section — focus on most significant signals
2. **Competency-based** — Use [[competency-matrix|Competency Matrix]] competencies
3. **Score format** — `**{Competency}** ({X.X}/5) : {Brief evidence}`
4. **Evidence brevity** — One line max in TOP; save details for Detailed Pros & Cons in BOTTOM
5. **Include "{Level} gap"** as explicit con when applicable

### Level Calibration

Always set **Target Level** and **Demonstrated Level** explicitly:
- If they match → "Hire at target"
- If demonstrated < target → "Downlevel to {lower}" or "Re-interview for {target}"
- If demonstrated > target → "Consider {higher} level offer"
- If inconclusive → state limitation in confidence rating

### Communication Breakdown

Don't use generic "Communication" — split into:
- **Remote Communication** — accent, audio, latency, team-fit risk
- **Technical Clarity** — concept articulation, structure of ideas
- **Structuring** — clarification before diving in (Level 4 signal)

A candidate can be 4/5 on Technical Clarity but 2/5 on Remote Communication — these have different implications.

### Limitations Section

Force honest evaluation framing:
- If only 20 min effective of 45 min → say so
- If tech issues impacted assessment → say so
- If certain areas couldn't be probed → list them
- Pair with Confidence rating (Low/Medium/High)

### Extra Miles Signal

Bar-raiser quality goes beyond minimum:
- Did they propose hardening beyond the question?
- Did they show curiosity about adjacent problems?
- Did they connect to broader patterns?

### Specific Evidence Citation

When pulling quotes/evidence, name specific concepts:

| Bad                                  | Good                                                                                   |
| ------------------------------------ | -------------------------------------------------------------------------------------- |
| "Demonstrated idempotency knowledge" | "Used epoch numbers + 2 trace IDs (write vs read, ordering by time)"                   |
| "Knows distributed systems"          | "Identified consumer-side connection pool saturation, not Redis itself, as root cause" |

### Score Granularity

Use 0.5 increments (e.g., 2.5/5, 3.5/5) for more nuanced assessments.

### Scoring Guide

| Score | Meaning                                  |
| ----- | ---------------------------------------- |
| 5/5   | Exceptional — exceeds level expectations |
| 4/5   | Strong — meets level expectations well   |
| 3.5/5 | Solid — meets bar with some gaps         |
| 3/5   | Adequate — meets minimum bar             |
| 2.5/5 | Borderline — slight gap                  |
| 2/5   | Weak — significant gap                   |
