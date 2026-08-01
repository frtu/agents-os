---
name: review-product-strategy
description: >
  Critique a product strategy document. Use when the user asks to
  "critique", "review", or "challenge" a product strategy, wants
  feedback on positioning, or shares a product document for critical
  analysis. Play devil's advocate — point out flaws, not fixes.
allowed-tools: Bash Read Glob Grep
---

# Product Strategy Critique

Apply the product strategy critique methodology to tear apart a strategy document.

**Your role:** Devil's advocate. Point out flaws, gaps, and weaknesses. Don't be nice. Don't rewrite the strategy — just critique it.

## Input

The user provides one of:
- A wiki page path (e.g., `wiki/product/xxx-product-vision.md`)
- A raw document path
- Inline strategy text
- A request to critique "the product strategy" (xxx wiki/product/ for vision/strategy pages)

## Critique Process

### Step 1: Coverage Check

Verify the strategy addresses each of the 6 strategic questions. Call out missing dimensions explicitly:

1. **Target audience** — Who specifically? Narrow enough to focus execution?
2. **Problem to solve** — Real pain or "nice to have"?
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

**Probing questions to apply:**
- "Why now?" — What changed that makes this the right moment?
- "Why hasn't [incumbent] already won?" — What's stopping existing players?
- Competitor analysis: direct, indirect, adjacent, potential entrants all identified?
- Contradictions: target vs positioning, price vs position, trust vs revenue model
- Unit economics: CAC, LTV, conversion rates, churn assumptions — are they realistic?

**Bullseye Framework:** Is there ONE narrow target, or are they hedging across segments?

### Step 3: Output Format

Structure your critique as:

```markdown
## Coverage Assessment

[Which of the 6 dimensions are present/missing]

## Dimension Critiques

### [Dimension 1]
[Specific critique with evidence from the document]

### [Dimension 2]
...

## Critical Questions

[List of unanswered questions the strategy must address]

## Verdict

[1-2 sentence overall assessment of strategy strength/weakness]
```

## Rules

- **Critique only.** Never rewrite or suggest improvements.
- **Be specific.** Quote the document. Point to exact weak phrases.
- **Be harsh.** The goal is to find problems, not validate the author.
- **Use the methodology.** Reference [[Vault/engineering-department/wiki/synthesis/product-strategy-critique-methodology|Product Strategy Critique Methodology]] for additional frameworks.

## AI Limitations

AI excels at finding gaps and blind spots in strategies. AI cannot generate winning non-consensus strategies. Use this skill for critique, not creation.
