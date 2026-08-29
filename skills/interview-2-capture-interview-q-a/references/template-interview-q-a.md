# Template: Interview Q&A Note

Copy this template to `wiki/projects/product-{product}/_interviews_/candidate-{slug}/{n}-{step}-qa-{slug}.md` and fill in placeholders.

Use this to **capture what was actually said** in an interview — a faithful, themed transcript of questions and answers. It is the raw-signal layer that a [[template-candidate-evaluation|Candidate Evaluation]] later scores against. Produce it from a transcript, an AI recruiting summary, or your own notes.

## What this is — and is NOT

| | Q&A Note (this template) | Candidate Evaluation |
|---|---|---|
| **Answers** | *"What was asked and what did they say?"* | *"How good was it, and do we hire?"* |
| **Voice** | Neutral capture — the candidate's answer, minimally editorialized | Judgment — scores, verdict, level calibration |
| **Grows into** | Feeds the evaluation | Feeds the hiring decision |
| **Bias** | Record everything relevant, even ambiguous | Take a position |

Keep judgment light here. A one-word **signal tag** per answer is allowed (it speeds the later write-up), but the full scoring, verdict, and recommendation belong in the evaluation, not here.

## Design principle: faithful, themed, dual-layer

- **Faithful** — capture the *substance* of each answer, including corrections, hedges, and "I don't know"s. Those are signal. Do not smooth them away or infer competence the candidate didn't show.
- **Themed, not chronological** — group questions by theme (motivation, technical deep-dive, behavioral…) so a reader can find the architecture discussion without scrubbing the whole timeline. Follow-ups stay nested under their parent question.
- **Dual-layer** — each answer is captured as **bullets** (the atomic points, close to what was said) and, where it earns its keep, a one-line **prose synthesis** (what the bullets add up to). Bullets preserve detail; prose gives the reader the gist in one pass.

---

## The template

```markdown
---
Category: projects
Tags: [hiring, interview-qa, candidate, {slug}, {product}, {level}, {step}]
Source links:
  - [[source-{slug}]]
  - [[1-candidate-{slug}]]
Created: {YYYY-MM-DD}
Last Updated: {YYYY-MM-DD}
---

# Interview Q&A: {Full Name}

**Role:** {Title} ({Level})
**Team:** {Product}
**Interview Step:** [[step-hire-{n}-{step}|{Step Name}]]
**Interviewer:** {Name}
**Date:** {YYYY-MM-DD}
**Source:** {Transcript / interviewer notes}

## TL;DR

{2-4 sentences: the shape of the conversation and the headline signals — what stood out, what wobbled. No scores.}

## Themes at a Glance

| Theme | Questions | Headline signal |
|-------|:---------:|-----------------|
| Intro & Motivation | {n} | {one phrase} |
| Technical Deep-Dive | {n} | {one phrase} |
| Impact & Achievements | {n} | {one phrase} |
| Behavioral & Ownership | {n} | {one phrase} |
| Candidate's Questions | {n} | {one phrase} |

---

## 1. Intro & Motivation

### Q: "{Question as asked}"
- {Answer point — atomic, close to what was said}
- {Answer point}
- {Answer point}

**In short:** {optional one-line prose synthesis.} · *Signal:* {✅ strong / ⚠️ mixed / ❌ weak / ➖ neutral}

### Q: "{Question}"
- {Answer point}
- {Answer point}

---

## 2. Technical Deep-Dive

### Q: "{Question}"
- {Answer point}
- {Answer point}

  ↳ **Follow-up: "{Probing follow-up}"**
  - {How they responded to the push — this is where depth or its absence shows}
  - {Correction / hedge / "I don't know" — capture verbatim-ish}

**In short:** {synthesis.} · *Signal:* {tag}

### Q: "{Question}"
- {Answer point}

---

## 3. Impact & Achievements

### Q: "{Question about a metric/outcome on their resume}"
- {Claimed outcome, with the number as they stated it}
- {Mechanism — how they say they achieved it}
- {What was theirs vs the team's, if it surfaced}

**In short:** {synthesis.} · *Signal:* {tag}

---

## 4. Behavioral & Ownership

### Q: "{Conflict / failure / pushback / pivot question}"
- {Situation}
- {What they did}
- {Outcome / learning}

**In short:** {synthesis.} · *Signal:* {tag}

---

## 5. Candidate's Questions

- "{Question the candidate asked}" — {what it reveals about their priorities}
- "{Question}" — {read}

---

## Notable Quotes

> "{Direct quote worth preserving verbatim — a crisp trade-off, a red flag, or a strong signal.}"

> "{Quote}"

## Open Threads / Not Covered

- {Planned topic that time ran out on — flag for a later round}
- {Ambiguous answer that needs follow-up before a decision}

## Related

- [[1-candidate-{slug}|Candidate Evaluation (Pre-Interview)]]
- [[{n}-evaluation-{slug}|Post-Interview Evaluation]] — scores this note feeds
- [[source-{slug}|Source Profile]]
- [[interviews-{product}|{Product} Hiring]]
```

---

## How to fill it correctly

Apply editorial judgment first — a short screen doesn't need five themes (see Minimal variant). Then follow the per-section rules.

### Frontmatter
- **`Tags`** — always lead with `hiring, interview-qa`; then `candidate`, the `{slug}`, `{product}`, `{level}`, `{step}`. This is what makes the note findable next to the candidate's other pages.
- **`Source links`** — link the source profile and the pre-interview candidate page so the note sits in the candidate's dossier. Leave a link plain text if the target page doesn't exist yet (check wiki-schema).
- **`Last Updated`** — bump whenever you add answers (e.g., a second pass over the transcript).

### Header block
State **Interviewer**, **Date**, and **Source** explicitly. The source matters: an AI summary is already condensed and may drop hedges — note it so a reader knows the capture is second-hand, not a raw transcript.

### TL;DR
*Write this last.* 2-4 sentences on the *shape* of the conversation and the headline signals. Describe, don't score — "strong on pipeline architecture, wobbled on Kafka internals" not "3.5/5 on system design." If you can't summarize the conversation without inventing judgment, you're drifting into the evaluation.

### Themes at a Glance
A scannable index so a reader jumps to the section they care about. The **Headline signal** is one phrase per theme, neutral. Update the question counts to match the sections below.

### Q&A sections (the spine)
This is the note. Rules:
- **Group by theme, not time.** Common themes: *Intro & Motivation*, *Technical Deep-Dive*, *Impact & Achievements*, *Behavioral & Ownership*, *Candidate's Questions*. Rename/add/drop to fit the actual interview (a system-design round might split *Requirements*, *High-Level Design*, *Distributed Systems*).
- **Question verbatim (or close).** Quote the question as asked — the framing often shapes the answer. Keep the interviewer's exact wording for probing questions.
- **Answer as atomic bullets.** One point per bullet, close to what the candidate actually said. Preserve numbers as they stated them ("1.86% orders/user"), and **preserve corrections and hedges** — "initially said pull, then corrected to push" is high-value signal that a smoothed summary destroys.
- **Nest follow-ups** under their parent with `↳`. Depth interviews live in the follow-ups; that's where you see whether the first answer was understanding or recall.
- **"In short" is optional prose.** Add the one-line synthesis when the bullets need a gist; skip it when they're already self-evident. This is the dual-layer: bullets for fidelity, prose for speed.
- **Signal tag is one glyph, not a paragraph.** `✅ strong / ⚠️ mixed / ❌ weak / ➖ neutral`. It's a bookmark for the evaluation author, not a verdict. If you're writing sentences of judgment here, move them to the evaluation.

### Capturing the candidate's questions
The questions a candidate asks are signal — record them and a short read of what they reveal (culture curiosity, operational focus, growth orientation). Don't skip this section; it's often the cheapest read on motivation and seniority.

### Notable Quotes
Pull 2-5 verbatim lines worth preserving exactly — a crisp trade-off, a revealing red flag, a strong ownership statement. Quotes are the evidence the evaluation will cite; capture them here so they aren't lost.

### Open Threads / Not Covered
Honesty section. List planned topics that time (or tech issues) cut off, and answers too ambiguous to score. This tells the next interviewer what to probe and stops the evaluation from over-claiming coverage.

### Related
Link the pre-interview candidate page, the post-interview evaluation this note feeds, the source profile, and the team hiring page. Resolve concept links against the existing wiki (per the vault CLAUDE.md) before adding them; unresolved names stay plain text.

---

## Conventions

- **Neutral capture over judgment.** When in doubt, record what was said and let the evaluation decide what it means.
- **Fidelity beats brevity for answers.** It's fine for a deep-dive answer to run long — detail is the point. Brevity lives in the TL;DR and prose synthesis, not in the bullets.
- **Corrections are gold.** A candidate who self-corrects, hedges appropriately, or says "I don't know" is giving you real signal — never edit it out to make the answer look cleaner.
- **One note per interview step.** A candidate with coding + system-design + team-match rounds gets three Q&A notes, each linked from the candidate page.
- **Signal tags ≠ scores.** Tags are navigational. Scores, level calibration, and the hire/no-hire call belong in [[template-candidate-evaluation|the evaluation]].

---

## Minimal Q&A Note

For a short screen or a single-topic round — drop the Themes table, Notable Quotes, and multi-section grouping. Keep the header, a flat Q&A list, and open threads.

```markdown
---
Category: projects
Tags: [hiring, interview-qa, candidate, {slug}, {product}, {step}]
Source links:
  - [[source-{slug}]]
Created: {YYYY-MM-DD}
Last Updated: {YYYY-MM-DD}
---

# Interview Q&A: {Full Name}

**Step:** {Step} · **Interviewer:** {Name} · **Date:** {YYYY-MM-DD} · **Source:** {Transcript / Mnotes}

## TL;DR

{2-3 sentences, neutral.}

## Q&A

### Q: "{Question}"
- {Answer point}
- {Answer point}

*Signal:* {✅ / ⚠️ / ❌ / ➖}

### Q: "{Question}"
- {Answer point}

## Open Threads

- {What wasn't covered / needs follow-up}

## Related

- [[source-{slug}|Source Profile]]
- [[interviews-{product}|{Product} Hiring]]
```
