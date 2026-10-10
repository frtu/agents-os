# Step: System Design (Step 3)

Loaded by `SKILL.md` when `{step}` is `system-design`. Overrides the generic question guide (SKILL.md step 6) where stated; everything else stays generic.

**Read first:** [[step-hire-3-system|Step 3]], [[interview-rubric-system-design|System Design Rubric]], and `question-bank-system-design` if it exists (reuse its problems as a base).

## Core rule

The guide is built around **one live design problem**, not a set of résumé retrospectives. Retrospective deep dives belong to `engineering-screen`. Mixing them in here is the most common failure.

The primary challenge sits at the **intersection of the round's load** (SKILL.md step 3b): built on the candidate's **strongest asset (3)**, but forcing the **highest-priority probe (2)**.

## What changes vs the generic guide

| Aspect | Generic guide | System Design |
|--------|---------------|---------------|
| Question mode | Tailored to résumé | **One live problem**, résumé used only as a bridge |
| Extra section | — | **Primary Challenge**, inserted between Risk Profile and Question Bank |
| Categories | 5-7, free | **A–G, following the phases of the one problem** |
| Interview shape | `{duration}` | ~60 min, ~15 questions picked, the rest as backups |

## Primary Challenge section

Insert into the question guide at the `{Step-specific section}` slot:

```markdown
## Primary Challenge: {Problem Name} ({key constraint, e.g. customer-facing, multi-region})

**Rationale:** {Why this problem: it sits at the intersection of the candidate's **greatest strength** ({asset}) and **flagged gap** ({concern}). Quote the JD/mission line it comes from.}

### Problem Statement

> "{The problem exactly as the interviewer will read it aloud — a concrete user, a concrete example query/action, and 2-3 numbered hard requirements (scale, latency/SLA, correctness, compliance). End with 'Walk me through your design.'}"

### Why this challenge
- **Directly relevant:** {which résumé system is the building block — and what's different now}
- **Ambiguity ({Target}):** {which requirements are left open to test requirements-gathering}
- **Hits the flagged gap:** {how it forces the central concern}
- **Correctness/stakes:** {what domain stakes force a hard trade-off}
- **{Floor} vs {Target} vs {Stretch} differentiator:** {Floor} describes …; {Target} owns …; {Stretch} frames …
```

## Question categories

Follow the phases of the one problem. Adapt names to the domain.

| # | Category | Purpose |
|---|----------|---------|
| A | Requirements Gathering — scope, SLA, correctness bar | Do they box the problem to numbers, or start building what they already know? |
| B | High-Level Architecture | Components with justified trade-offs |
| C | {Domain-critical surface, e.g. AI/NL2SQL, payments ledger} — **CRITICAL FOCUS** if it carries a concern | Production-grade vs prototype |
| D | Distributed Systems / Multi-Region / Consistency — **CRITICAL FOCUS** if it carries a concern | The flagged gap |
| E | Scale, Performance & Cost | "Load grows 20× — what breaks first?" |
| F | Reliability & Correctness | Failure → detection → degradation |
| G | Technical Direction, Build-vs-Buy & Altitude — **{Target}/{Stretch} differentiator** | Direction set vs executed; context-fit build-vs-buy; mentoring; one deliberate push-back question |

## Rules

- Every question is **about the primary challenge**. Use the résumé only as a *bridge*: "You built {X} at {Company} — what transfers here, and what doesn't?" At most ~3 bridge questions, and at most **one** pure retrospective (the direction/adoption story in G).
- The Interviewer note must warn against the comfortable retrospective and demand numbers (SLA, QPS, regions, staleness budget), not architecture nouns.
- Include one **push-back** question ("I'll push back: skip {safeguard}, ship now — convince me otherwise or agree").
- Flow: ~60 min, with time ranges summing to exactly 60. Pick ~15 questions and list the rest as backups.

## Red flag to pre-load

The candidate redesigns the system they already built: same components, same numbers, no new requirements asked. Prepare a "what's different here?" redirect for Q1–Q3.

## Checklist additions

- [ ] Exactly one Primary Challenge, at the intersection of asset (3b-3) and probe (3b-2).
- [ ] Problem statement is speakable as-is: a concrete user, an example, and 2-3 numbered hard requirements.
- [ ] Categories follow the problem's phases. ≤3 bridge questions, ≤1 pure retrospective, 1 push-back.
