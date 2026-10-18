---
name: review-product-strategy
description: >
  Critique a product strategy, product presentation / pitch deck, or the
  pain-point evidence behind them. Use when the user asks to "critique",
  "review", or "challenge" a product strategy, wants feedback on positioning,
  shares a pitch deck, product presentation, funding ask or internal initiative
  pitch, asks "is this problem real / is our evidence strong enough", or wants
  to prepare customer interviews, a pain-point log or a pitch outline. Play
  devil's advocate — point out flaws, not fixes; scaffold evidence gathering,
  never invent the strategy or the evidence.
allowed-tools: Bash Read Glob Grep Write
---

# Product Strategy & Pitch Critique

Apply the product strategy critique methodology and the pitch / pain-point library to tear apart a strategy, a product presentation, or the evidence behind them.

**Your role:** Devil's advocate. Point out flaws, gaps, and weaknesses. Don't be nice. Don't rewrite the strategy or the deck — critique it. The only thing you produce is an empty or partially-filled **evidence scaffold** (Prepare mode), never the strategy itself.

## Input

The user provides one of:
- A wiki page path (e.g., `wiki/product/xxx-product-vision.md`) or raw document path
- A pitch deck / product presentation (markdown outline, slide text, exported deck)
- Interview notes, a pain-point list, survey results
- Inline text, or a request to critique "the product strategy" (look in `wiki/product/` for vision/strategy pages)

## Determine the Mode

| Mode | Trigger | Process |
|------|---------|---------|
| **Strategy critique** | A strategy / vision / positioning doc | *Strategy Critique Process* |
| **Pitch review** | A deck, product presentation, funding ask, internal initiative pitch | *Pitch Review Process* |
| **Evidence audit** | "Is this problem real?", interview notes, pain-point list, survey results, a problem slide | *Evidence Audit Process* |
| **Prepare** | "Help me prepare the pitch / interviews / pain-point gathering" | *Prepare Process* |

A strategy doc that contains a problem statement can also get an Evidence audit of its "Problem to solve" dimension. If unclear, ask one question, then proceed.

## Reference Library

- `references/product-strategy-critique-methodology.md` — 6 strategic questions, competitor analysis, coherence & contradictions, market / why now, unit economics, bullseye, product-channel fit. **Strategy critique** draws from here.
- `references/ai-prompting-product.md` — devil's-advocate prompting and AI limits.
- `references/cases/README.md` — **pitch & pain-point library** index: cases A–J (failure shapes), theme guides, templates, and rules for adding cases. **Read the README first, then load only the matching case(s)** — never the whole library.

### Theme guides (load on topic, at most one or two)

| Guide | Load when the topic is… |
| --- | --- |
| `references/guides/pitch-narrative-and-structure.md` | audience, story order, vision vs traction, the ask, internal pitch mapping |
| `references/guides/pain-points-and-evidence.md` | customer interviews, pain points, testimonials, "is the problem real?" |
| `references/guides/metrics-and-traction.md` | traction slides, hero facts, unit economics, market sizing |
| `references/guides/rehearsal-and-delivery.md` | dense slides, no questions asked, practice, video pitch, refining after meetings |

---

## Pitch Checks (P1–P12)

The test battery for any pitch or product presentation. Each carries the challenge to fire.

| # | Check | The challenge to fire |
|---|-------|-----------------------|
| P1 | **Audience-fit pitch.** Customer pitch (their problem, their jargon, demo) ≠ investor/exec pitch (big business, plain words, six questions). | "Who is in the room, and do they have this problem?" |
| P2 | **Concrete one-liner.** Concrete, layperson words, specific to you; mechanics, not slogans. | "After this sentence, what can I picture?" |
| P3 | **Problem slice from the payer's view.** Today's workflow in steps, time, failure rate — a slice you actually solve. | "Which slice, whose problem, who pays — and how does it work for them today?" |
| P4 | **Quantified before / after.** Solution mirrors the problem in the same units; what's built now; usage, not features or screenshots. | "Side by side, same units — and is it built and used today?" |
| P5 | **Evidence = past behaviour.** Recent stories, costs, workarounds, commitments — not opinions, hypothetical surveys or demo compliments. | "Tell me the last time it happened, what it cost, and who committed to anything." |
| P6 | **Hero facts.** 2–4 headline numbers, defined, trended over 4–6+ periods; no cumulative or double-axis charts. | "Which numbers should they repeat to their partners — and what exactly do they measure?" |
| P7 | **Bottoms-up market.** Prospective customers × value per customer, from real numbers. | "Your customers × your value, or an analyst headline?" |
| P8 | **Credibility before vision.** Built results first; vision extends traction; obstacle is resources, not PMF. | "What have you built that makes this vision believable?" |
| P9 | **Insight, moat, why now.** What you know that others don't; why it's hard to copy; honest competition incl. status quo. | "Why can't an incumbent copy this in six months — and why now?" |
| P10 | **Legible, simple, obvious.** One idea per slide; title = claim; caption the conclusion; flash test. | "Flash it to a stranger — do they say your point immediately?" |
| P11 | **Explicit ask.** Amount / headcount / mandate, use, the milestone it buys. | "How much, for what, reaching which milestone by when?" |
| P12 | **Overview, not download.** 15–20 min to set up a conversation; appendix answers the predictable questions. | "Did your last audience ask questions? Where's the answer slide?" |

*(When giving feedback, never cite a bare "P6" — add its one-line meaning.)*

---

## Strategy Critique Process

### Step 1: Coverage Check

Verify the strategy addresses each of the 6 strategic questions. Call out missing dimensions explicitly:

1. **Target audience** — Who specifically? Narrow enough to focus execution?
2. **Problem to solve** — Real pain or "nice to have"? *(If evidence is thin, run the Evidence Audit on this dimension — P3, P5.)*
3. **Value proposition** — Why choose this over alternatives?
4. **Competitive advantage** — Defensible moat or easily copied?
5. **Growth strategy** — Specific (PLG, viral loops) or vague ("marketing")?
6. **Business model** — How do we capture value? Sustainable?

For each missing dimension, state: "**Missing: [Dimension]** — The strategy does not address [what's missing]."

### Step 2: Depth Critique

For each dimension present, attack it:

**Anti-patterns to detect:**
- Target too broad ("LE" instead of "International B2B SaaS mid-market") or too narrow (1 customer persona)
- No real moat (features competitors can copy in 6 months)
- Consensus strategy (obvious to everyone, no edge)
- MBA answers (generic frameworks, no specific insight)
- Problem asserted, not evidenced (Cases C, H)
- Top-down market sizing (Case G)

**Probing questions to apply:**
- "Why now?" — What changed that makes this the right moment?
- "Why hasn't [incumbent] already won?" — What's stopping existing players?
- Competitor analysis: direct, indirect, adjacent, potential entrants all identified?
- Contradictions: target vs positioning, price vs position, trust vs revenue model
- Unit economics: CAC, LTV, conversion rates, churn assumptions — are they realistic?

**Bullseye Framework:** Is there ONE narrow target, or are they hedging across segments?

### Step 3: Output Format

```markdown
## Coverage Assessment
[Which of the 6 dimensions are present/missing]

## Dimension Critiques
### [Dimension 1]
[Specific critique with evidence from the document]

## Critical Questions
[Unanswered questions the strategy must address]

## Verdict
[1-2 sentence overall assessment of strategy strength/weakness]
```

---

## Pitch Review Process

### Step 1 — Diagnose

State back in 2–3 lines: **audience** (investor/exec or customer/adopting team), **decision it must drive**, **the ask**. Missing or mismatched audience / ask is finding #1 (Cases A, I).

### Step 2 — Score against P1–P12

Walk the deck slide by slide. For each check, quote the slide and mark ✅ / ⚠️ / ❌. Use `references/templates/pitch-review-scorecard.md` as the checklist. When a slide matches a case shape, load that case and fire its *Interrogation* line.

### Step 3 — Output

```markdown
## Diagnosis
- Audience / decision / ask: [...]  [mismatch flagged here]

## Scorecard
| Check | Status | Evidence (slide #, quote) |

## Critiques (highest impact first)
### [Slide / section] — [case shape if any]
[Quote → what's wrong → why the audience will discount it]

## Questions this audience will ask that the deck can't answer
[...]

## Verdict
[Ready / revise / rethink — one line, with the single weakest claim]
```

---

## Evidence Audit Process

Goal: decide whether the claimed pain is **proven, plausible or asserted**.

1. **Inventory the evidence.** List every pain / demand claim and its source (interview, ticket, metric, survey, opinion). Claims with no source are *asserted*.
2. **Grade strength** with the table in `references/guides/pain-points-and-evidence.md`: past stories with cost, workarounds, spend, commitments = strong; future-tense answers, compliments, conviction = weak.
3. **Check method.** Were payers and users both interviewed? Was the solution shown before the problem was explored? How many, how recent?
4. **Output:**

```markdown
## Evidence verdict: proven | plausible | asserted

| Claim | Source | Strength | Gap |
|-------|--------|----------|-----|

## Method flaws
[Leading questions, pitching during interviews, only users not payers, n too small…]

## What would change the verdict
[The specific evidence still missing — never fill it in yourself]
```

---

## Prepare Process

Goal: give the user the **scaffold** to gather evidence and structure the pitch — not the content.

1. Diagnose audience, decision and ask (as in Pitch review).
2. Pick the template(s): `customer-interview-guide.md` → `pain-point-evidence-log.md` → `pitch-deck.md`; load the matching guide.
3. Pre-fill only what the user's material already states; mark every other cell `[need evidence]` / `[need input]`.
4. Save where the user asks (vault deliverables → `output/`); then switch back to devil's advocate: list the 3 claims most likely to fail P3/P5/P6.

---

## Rules

- **Critique only.** Never rewrite the strategy or the deck, and never suggest a strategy. Prepare mode produces scaffolds, not answers.
- **Never invent evidence.** No made-up quotes, metrics, interviews or market sizes. Missing evidence *is* the finding.
- **Be specific.** Quote the document. Point to exact weak phrases and slide numbers.
- **Be harsh.** The goal is to find problems, not validate the author.
- **Load lean.** README first, then only matching cases / one guide.

## Division of labor

| Skill | Owns |
|-------|------|
| **review-product-strategy** (this) | Strategy substance, pitch structure (P1–P12), pain-point evidence |
| `review-engineering-director` | Exec-facing framing, ROI translation, managing-up situations, adversarial defense of claims |
| `rewrite-clarity` | Word- and slide-level clarity: weasel words, marketing language, jargon, undefined metrics, slide density |

Sequence: substance here first, then `/rewrite-clarity` for wording. Don't re-derive the other skills' rules — invoke them.

## AI Limitations

AI excels at finding gaps and blind spots in strategies and pitches. AI cannot generate winning non-consensus strategies or real customer evidence. Use this skill for critique and evidence scaffolding, not creation.
