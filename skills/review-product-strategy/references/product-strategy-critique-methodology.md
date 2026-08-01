---
Category: synthesis
Tags: [synthesis, product-strategy, critique, methodology, ai-prompting, devil-advocate]
---

# Product Strategy Critique Methodology

A comprehensive framework for critiquing product strategies, combining the 6 strategic questions framework with AI-assisted devil's advocate techniques.

## The 6 Strategic Questions

Every product strategy must address these dimensions :

| #   | Strategic Question        | What to Evaluate                                                           |
| --- | ------------------------- | -------------------------------------------------------------------------- |
| 1   | **Target Audience**       | Who specifically are we serving? Is it narrow enough to focus execution?   |
| 2   | **Problem to Solve**      | What pain point are we addressing? Is it a real pain or "nice to have"?    |
| 3   | **Value Proposition**     | Why should customers choose us over alternatives?                          |
| 4   | **Competitive Advantage** | How do we win against competitors? Is the moat defensible?                 |
| 5   | **Growth Strategy**       | How do we scale? Is it specific (PLG, viral loops) or vague ("marketing")? |
| 6   | **Business Model**        | How do we capture value? Is monetization sustainable?                      |

## Competitor Analysis Framework

A rigorous framework for evaluating competitive landscape claims in product strategies. Most strategies fail the competitor test not because they ignore competition, but because they analyze it superficially.

### Deep Dive Questions

Identify ALL competitor types, not just the obvious ones:

| Competitor Type        | Definition                                   | Questions to Ask                                                                            |
| ---------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **Direct**             | Same solution, same problem                  | Who else solves this exact problem the same way?                                            |
| **Indirect**           | Different solution, same problem             | What other approaches do customers use today? (spreadsheets, manual processes, consultants) |
| **Adjacent**           | Same solution, different but related problem | Who uses similar technology for a neighboring use case? Could they expand?                  |
| **Potential Entrants** | Incumbents who could add this feature        | Which established players could ship this as a feature in 6 months?                         |

**Red flag:** If the strategy only lists direct competitors, the analysis is incomplete.

### Competitor Landscape Mapping Template

| Competitor    | Type      | Their Strengths | Their Weaknesses | Why We Win | Why We Might Lose |
| ------------- | --------- | --------------- | ---------------- | ---------- | ----------------- |
| [Name 1]      | Direct    |                 |                  |            |                   |
| [Name 2]      | Indirect  |                 |                  |            |                   |
| [Name 3]      | Adjacent  |                 |                  |            |                   |
| [Incumbent X] | Potential |                 |                  |            |                   |

**Usage:** Fill this out for each competitor mentioned. If "Why We Might Lose" is empty or weak, the analysis lacks rigor.

### "Why Haven't Incumbents Won?" Questions

For every major incumbent or well-funded player in the space:

1. **If [Incumbent X] added this feature tomorrow, what stops them from winning?**
   - Is it distribution? (You don't have it either)
   - Is it technology? (Usually not defensible long-term)
   - Is it DNA/focus? (Strongest answer)

2. **What do established players know that you don't?**
   - They've likely tried this or considered it
   - Why did they pass? Market too small? Execution too hard? Doesn't fit their model?

3. **What's preventing well-funded competitors from replicating in 6 months?**
   - Network effects? (Takes time to build)
   - Proprietary data? (Where does it come from?)
   - Regulatory moat? (Rare and hard to build)
   - Distribution? (Usually incumbent advantage)

4. **Why hasn't [Obvious Incumbent] already solved this?**
   - "They're slow" is not a strategy
   - "They don't care about this segment" — why not? Too small? Too hard?

### Historical Failure Analysis

Every "new" idea has probably been tried before. Investigate:

| Question                                                              | Why It Matters                |
| --------------------------------------------------------------------- | ----------------------------- |
| **What companies tried this before and failed?**                      | Learn from their mistakes     |
| **Why did they fail?** (acquisition, pivot, shutdown, slow death)     | Understand the failure mode   |
| **What do you know that they didn't?**                                | Must have a specific answer   |
| **What's different now?** (market timing, technology, behavior shift) | "We're smarter" is not enough |

**Examples to research:**
- LearnVest (personal finance) — acquired by Northwestern Mutual, product eventually shut down
- Mint (personal finance) — acquired by Intuit, now being sunset
- Previous attempts in your space — find them via Crunchbase, Google, talking to industry veterans

**If you can't find any prior attempts:** Either you're not looking hard enough, or the market is so unattractive that no one bothered.

### Competitor Red Flags

Watch for these warning signs in competitive analysis:

| Red Flag                                       | What It Reveals                                | Critique Question                                                 |
| ---------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------- |
| **No specific competitor names**               | "Competitors" is generic hand-waving           | Name three direct competitors and their market share              |
| **Only mentioning weak competitors**           | Cherry-picking to look good                    | Who's the strongest player you're afraid of?                      |
| **No answer to "why haven't incumbents won?"** | Ignoring the elephant in the room              | What stops [Biggest Player] from shipping this tomorrow?          |
| **Ignoring adjacent markets**                  | Blind spot to disruption                       | Who in adjacent spaces could pivot into this?                     |
| **"No direct competition"**                    | Either a massive opportunity or a warning sign | Why has no one built this? Market too small? Problem not painful? |
| **Competitor moat dismissed too easily**       | "They're slow" / "They don't get it"           | How long would it take them if they decided to compete?           |

**Historical Failure Examples:**

| Company              | What Happened                                             | Lesson                                                                 |
| -------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------- |
| **LearnVest**        | Acquired by Northwestern Mutual (2015), product shut down | "Democratizing financial planning" is harder than it looks             |
| **Mint**             | Acquired by Intuit, being sunset (2024)                   | Even the #1 personal finance app couldn't build a sustainable business |
| **Personal Capital** | Acquired by Empower, pivoted to human advisors            | Tools alone don't retain HNW clients                                   |

**Key Critique Questions:**
- If Wealthfront/Betterment added this feature tomorrow, what stops them winning?
- What does this strategy know that LearnVest didn't?
- Why would Empower (with existing HNW relationships) not just ship this?

### AI Prompt for Competitor Analysis

Use this prompt to systematically evaluate competitive claims:

```
Analyze the competitive landscape in this strategy:

1. **Competitor Coverage:**
   - Are direct, indirect, adjacent, and potential entrant competitors identified?
   - Are specific company names mentioned, or just generic "competitors"?

2. **Incumbent Question:**
   - Is there an answer to "why haven't incumbents already won?"
   - Is the answer specific and credible, or hand-wavy?

3. **Historical Context:**
   - Are prior attempts in this space acknowledged?
   - Is there a clear answer to "what's different now?"

4. **Red Flags:**
   - Any of these present?
     - Only weak competitors mentioned
     - No incumbent analysis
     - "No competition" claim
     - Generic competitive advantages (technology, team, speed)

Be specific. Name what's missing and why it matters.
```

## Common Strategy Pitfalls

Watch for these anti-patterns:

| Pitfall                | What It Looks Like                                         | AI Can Detect? |
| ---------------------- | ---------------------------------------------------------- | -------------- |
| **Target too broad**   | "We serve everyone" = no focus                             | Yes            |
| **No real moat**       | "Sophisticated model" — complexity ≠ competitive advantage | Yes            |
| **Consensus strategy** | Following what everyone else does                          | Sometimes      |
| **MBA answer**         | Sounds smart but not battle-tested                         | Yes            |

## Strategic Coherence & Contradiction Detection

Strategies often fail not because individual elements are weak, but because elements **contradict each other**. A coherent strategy tells one story; an incoherent strategy tries to tell multiple conflicting stories simultaneously.

### Common Strategic Contradictions Checklist

| Contradiction Pattern      | Example                                                            | Why It's a Problem                             |
| -------------------------- | ------------------------------------------------------------------ | ---------------------------------------------- |
| **Target vs Positioning**  | Target sophisticated users but claim automation removes complexity | Can't optimize for both control AND simplicity |
| **Price vs Position**      | Position as "democratizing" but price for premium market           | Democratizing means accessible pricing         |
| **Customer vs Competitor** | Position against advisors but also target advisors as customers    | You can't disrupt and serve the same people    |
| **Depth vs Simplicity**    | Build complexity as moat but claim simplicity as benefit           | Pick one: power tool or easy tool              |
| **Trust vs Revenue**       | Claim objectivity but plan affiliate/referral revenue              | Financial incentives create distrust           |
| **B2C vs B2B**             | Consumer freemium and enterprise tiers in same strategy            | Different sales motions, different products    |
| **Focus vs Breadth**       | "Initial target" has 3+ segments                                   | Multiple segments = no focus                   |

### Coherence Test Questions

Use these questions to test whether the strategy is internally consistent:

1. **Segment conflict:** If I optimize for Segment A, do I alienate Segment B?
2. **Pricing alignment:** Does the pricing match the positioning?
3. **Channel fit:** Does the growth strategy reach the target audience?
4. **Moat relevance:** Does the moat protect against the stated competitors?
5. **Model support:** Does the business model support the claimed value proposition?

If any answer is "no," there's an internal contradiction that needs resolution.

### The "One Business" Test

A good strategy describes **ONE coherent business**:

| Dimension             | Requirement                   |
| --------------------- | ----------------------------- |
| **Customer**          | One primary customer          |
| **Problem**           | One primary problem           |
| **Value Proposition** | One primary value proposition |
| **Channel**           | One primary channel           |
| **Revenue Model**     | One primary revenue model     |

**If the strategy describes multiple businesses masquerading as one, call it out.** Multiple targets, multiple value props, and multiple revenue models usually mean the team hasn't made hard choices yet.

### Contradiction Red Flags

Specific phrases that signal incoherence:

| Red Flag Phrase                                   | What It Reveals                                     |
| ------------------------------------------------- | --------------------------------------------------- |
| "Primary, secondary, and tertiary segments"       | No clear focus — trying to serve everyone           |
| "We serve both consumers AND enterprises"         | Two different businesses with different GTM         |
| "Freemium with enterprise tier"                   | Conflicting sales motions (self-serve vs sales-led) |
| "We're democratizing [X]" + "$50+/month pricing"  | Democratizing is incompatible with premium pricing  |
| "Objective recommendations" + "affiliate revenue" | Financial incentives undermine trust claims         |

### AI Prompt for Contradiction Detection

Use this prompt to systematically identify internal contradictions:

```
Identify internal contradictions in this strategy:

1. **Target-Value Match:** Does the target audience match the value proposition?
2. **Price-Position Match:** Does the pricing match the positioning?
3. **Growth-Target Match:** Does the growth strategy reach the stated target?
4. **Business Count:** Are there multiple businesses disguised as one?
5. **Trust-Model Match:** Does the business model create conflicts with trust claims?

For each contradiction found:
- Quote the specific conflicting statements from the strategy
- Explain why they cannot both be true
- Suggest which direction to choose

Be specific. Use exact quotes from the strategy document.
```

## Market & Regulatory Awareness

Strategies often reveal blind spots in market understanding. This section helps critics identify gaps in regulatory awareness, behavioral economics considerations, and market timing.

### Regulatory Considerations by Industry

Different industries carry different regulatory burdens. A strategy that ignores compliance costs in a regulated industry signals a dangerous blind spot.

| Industry            | Key Regulatory Questions                                           | Red Flags                                                    |
| ------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------ |
| **Healthcare**      | HIPAA implications? FDA classification?                            | Health data without privacy framework                        |
| **Insurance**       | State licensing requirements?                                      | Insurance recommendations without licensing                  |
| **Fintech/Finance** | Does this constitute investment advice requiring RIA registration? | "Personalized recommendations" without compliance discussion |
| **General**         | Data privacy (GDPR, CCPA)?                                         | No mention of data handling                                  |

### Behavioral Economics Lens

Most strategies assume rational, motivated users. Reality is different. Critique whether the strategy accounts for real human behavior.

| Behavioral Barrier       | Definition                                           | Critique Question                                                |
| ------------------------ | ---------------------------------------------------- | ---------------------------------------------------------------- |
| **Present Bias**         | People overweight immediate costs vs future benefits | Will users actually engage with long-term projections?           |
| **Temporal Discounting** | Future outcomes feel less real than present          | How do you make 30-year projections feel urgent?                 |
| **Complexity Aversion**  | People avoid cognitively demanding tasks             | Is sophisticated modeling what users WANT or what founders WANT? |
| **Status Quo Bias**      | People stick with current behavior                   | What triggers behavior change?                                   |
| **Optimism Bias**        | People underestimate personal risk                   | Do projections account for realistic downside scenarios?         |

**Ask:** Does the strategy assume rational, motivated users, or does it account for real human behavior?

### Market Dynamics Questions

Questions to probe market understanding:

- **Market Timing ("Why Now?")**: What technology, behavioral, or regulatory shift makes this moment right?
- **Market Size Reality Check**: Is the addressable market as large as claimed? What % would actually pay?
- **Incumbent Awareness**: What do incumbents know that you don't? Why haven't they already won?
- **Historical Pattern**: What similar products have tried and failed? What's different now?

### "Why Now?" Framework

Every winning strategy needs a "why now" answer. Timing matters as much as the idea itself.

| "Why Now?" Type      | Example                                                | Strength                  |
| -------------------- | ------------------------------------------------------ | ------------------------- |
| **Technology Shift** | "GPT-5 enables natural language queries"               | Strong if genuinely new   |
| **Behavioral Shift** | "COVID increased comfort with digital tools"           | Strong if verified        |
| **Regulatory Shift** | "Open banking APIs now mandated in EU"                 | Strong and defensible     |
| **Market Shift**     | "Mint shutdown creates opportunity"                    | Moderate - reactive       |
| **No "Why Now?"**    | "Financial planning has always been needed"            | Weak - no timing catalyst |

### Market Awareness Red Flags

| Red Flag                                       | What It Reveals                                   |
| ---------------------------------------------- | ------------------------------------------------- |
| No regulatory discussion in regulated industry | Founder may not understand compliance costs       |
| Assumes rational user behavior                 | Ignores behavioral economics realities            |
| No "why now" answer                            | Timing is luck, not strategy                      |
| Market size based on TAM, not SAM              | Likely 10-100x overestimate                       |
| "No direct competition"                        | Either a massive opportunity or willful blindness |

## Unit Economics & Business Model Rigor

Unit economics reveal whether a business can actually make money. Most strategies discuss revenue models without verifying the math works.

### Specific Questions to Ask

| Metric                              | Question                                           | Why It Matters                          |
| ----------------------------------- | -------------------------------------------------- | --------------------------------------- |
| **CAC (Customer Acquisition Cost)** | What does it cost to acquire one paying customer?  | Must be lower than LTV                  |
| **LTV (Lifetime Value)**            | Expected revenue per customer over their lifetime? | Must justify CAC                        |
| **Conversion Rate**                 | What % of free users become paid?                  | Freemium typically 1-5%                 |
| **Payback Period**                  | How long to recover CAC?                           | Should be <12 months for SaaS           |
| **Gross Margin**                    | Revenue minus cost of goods sold?                  | Plaid APIs, infrastructure costs add up |
| **Churn Rate**                      | What % of users leave per month?                   | >5% monthly churn kills SaaS            |

### Freemium Economics Reality Check

| Assumption        | Typical Reality                  | Red Flag If...              |
| ----------------- | -------------------------------- | --------------------------- |
| Conversion rate   | 1-5% for consumer SaaS           | Strategy assumes >10%       |
| Monthly churn     | 3-8% for consumer apps           | No churn discussion         |
| CAC for fintech   | $50-200 through content          | "Viral growth" assumed      |
| LTV for $15/month | ~$150 at 10-month average tenure | Business model ignores this |

### Unit Economics Red Flags

- No CAC estimate despite detailed pricing
- "Viral growth" without viral coefficient calculation
- Freemium model without conversion rate assumption
- Enterprise pricing without sales cost discussion
- Affiliate revenue as primary path without conflict acknowledgment

## Target Audience Focus (Bullseye Framework)

A common strategy failure is targeting too many segments. The Bullseye Framework forces focus on ONE narrow target.

### The Bullseye Principle

A winning strategy has ONE narrow target, not concentric circles of "primary, secondary, tertiary" segments.

```
WRONG (Peanut Butter Strategy):
├── Primary: Dual-income professionals ($150K-$500K)
├── Secondary: FIRE enthusiasts  
└── Tertiary: Financial advisors

RIGHT (Bullseye Strategy):
└── One Segment: First-time homebuyers in SF Bay Area, 
    tech workers, age 28-35, HHI $200K-$300K, 
    planning purchase in next 6-12 months
```

### Focus Violation Detector

| Violation                      | Example                        | Problem                                   |
| ------------------------------ | ------------------------------ | ----------------------------------------- |
| **Multiple segments**          | "Primary, secondary, tertiary" | Can't optimize for 3 different needs      |
| **Huge demographic range**     | "Ages 30-50" (20-year span)    | Includes completely different life stages |
| **Income ranges too wide**     | "$150K-$500K" (3.3x range)     | Different financial psychology            |
| **B2C + B2B in same strategy** | Consumers AND advisors         | Different products, channels, compliance  |

### Narrowing Questions

Ask: Can you narrow further?

- What is the SINGLE persona who will be your first 100 paying users?
- What is the ONE triggering event that causes them to search for a solution?
- What is the ONE channel where you can reach them efficiently?
- What is the ONE use case you will own completely before expanding?

### Product-Channel Fit (Reforge Framework)

The product must be molded to the PRIMARY distribution channel:

| Channel              | Product Shape Required                                      |
| -------------------- | ----------------------------------------------------------- |
| **SEO**              | Content-rich, keyword-targeted landing pages                |
| **Paid Acquisition** | Clear value prop, fast time-to-value, measurable conversion |
| **Virality**         | Built-in sharing mechanics, network effects                 |
| **Sales**            | Demo-able, clear ROI story, enterprise features             |
| **Community**        | Discussion-worthy, identity-forming, shareable              |

**Critical question:** If the strategy lists multiple channels without prioritizing one, it has no product-channel fit strategy.

## Good vs Bad Examples

| Aspect               | Good                                                             | Bad                                                 |
| -------------------- | ---------------------------------------------------------------- | --------------------------------------------------- |
| **Target Audience**  | "Dual-income couples aged 30-40 with $100K+ income, first child" | "Professionals, retirees, and advisors" (too broad) |
| **Competitive Moat** | "Network effects from shared financial data"                     | "Sophisticated model" (anyone can build)            |
| **Growth Strategy**  | "Product-led growth via viral sharing features"                  | "Marketing" (not specific)                          |

## Core Critique Principle

> **AI gives consensus-driven output. Winning strategies require non-consensus, opinionated bets.**

When critiquing, always ask:
- Is this a **non-consensus bet** or just conventional wisdom?
- Is the differentiation **defensible** or can anyone copy it?
- Is the target **specific enough** to focus execution?

## AI Critique Workflow

Set up a systematic critique workflow:

### 1. Train AI on Excellence

Load product strategy best practices before critiquing:
- Michael Porter's competitive strategy framework
- Reforge course content
- Examples of well-critiqued strategies

### 2. Set Devil's Advocate Mode

Override AI's tendency to be nice:

```
Your task is to play devil's advocate and point out flaws or limitations 
in the provided product strategy. Don't be nice! Point out in detail why 
the product strategy may not work, what questions remain unaddressed, 
and where the strategy falls short.
```

### 3. Submit and Iterate

First output is a draft. Critique, refine, re-critique.

## Complete Critique Prompt

Use this prompt for comprehensive product strategy critique:

```
Your task is to play devil's advocate and point out flaws or limitations 
in the provided product strategy. Don't be nice! Point out in detail why 
the product strategy may not work, what questions remain unaddressed, 
and where the strategy falls short.

## Step 1: Coverage Check

Verify the strategy addresses each strategic question. If missing, call it out:

1. Target audience — Is it specific enough to focus execution?
2. Problem to solve — Is it a real pain point or a "nice to have"?
3. Value proposition — Why should customers choose this over alternatives?
4. Competitive advantage — Is the moat defensible or easily copied?
5. Growth strategy — Is it specific (PLG, viral loops) or vague ("marketing")?
6. Business model — How does value capture work?

## Step 2: Depth Critique

For each dimension present, critique using these lenses:

**Anti-patterns to detect:**
- Target too broad ("we serve everyone")
- No real moat (complexity ≠ advantage)
- Consensus strategy (what everyone else is doing)
- MBA answer (sounds smart, not battle-tested)

**Questions to ask:**
- Is this a non-consensus bet or conventional wisdom?
- Can a well-funded competitor copy this in 6 months?
- What would make customers switch FROM this product?

## Step 3: Missing Considerations

Call out what's NOT addressed:
- Execution risk — what's hardest to build?
- Market timing — why now?
- Team fit — why is this team uniquely suited?
- Failure modes — what kills this strategy?
```

## Claude Project Setup

For repeated critiques, create a Claude Project:

| Component               | Content                                                              |
| ----------------------- | -------------------------------------------------------------------- |
| **System Instructions** | Devil's advocate prompt above                                        |
| **Project Knowledge**   | Product strategy best practices, Porter's framework, Reforge content |
| **Examples**            | Well-critiqued strategy documents                                    |

**Result:** Every new conversation starts with expert context, producing consistent high-quality critiques.

## AI Limitations

| Dimension | AI Capability                                       |
| --------- | --------------------------------------------------- |
| Vision    | **Weak** — can't generate non-consensus, bold ideas |
| Strategy  | **Research & Critique** — not generation            |
| Design    | **Strong** — insights, prototyping                  |
| Execution | **Strong** — automation                             |

**Key insight:** AI excels at **critiquing** strategies (finding gaps, blind spots, generic thinking) but cannot **generate** winning strategies. Use it for the critique, not the creation.

## Related

- [[ai-prompting-product|AI Prompting for Product]] — Core AI prompting techniques
