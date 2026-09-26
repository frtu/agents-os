# Tech Product Definition — template & authoring guide

A reusable structure for a **product-definition / vision proposal**: the doc that argues a new technical product should exist, defines what it is, and asks for the resources to build it. Extracted from a real "one-system-to-rule-them-all" search proposal and upgraded with the director's judgement lens.

Use it in **Produce mode** to author, or as a checklist in **Review mode** to see what a draft is missing. It pairs with worked **Case A — the boil-the-ocean vision with no wedge** (`../cases/a-product-definition.md`), the failure this template is built to prevent.

---

## How to use this file

Each section below has three parts:

- **Insight it must deliver** — the one thing the reader should *know or decide* after reading it. If a section doesn't move the reader, cut it.
- **Style & format** — how it should read and look on the page.
- **Questions to answer** — fire these at yourself (or the author). A section is done when every question has a concrete answer — a **number and a name**, not an adjective. An unanswered question is a hole the real audience will find first.

**Golden rule (the whole doc in one line):** a product-definition doc is judged by its **wedge** (the one job it wins first) and its **ask** (the one decision it demands), never by the breadth of its vision. Everything else is support.

---

## The structural spine

Order matters. This sequence front-loads the decision and earns the detail:

1. Metadata & status
2. Bottom line (BLUF)
3. Why now
4. Background — assets, status quo, opportunity
5. The product — identity & capabilities
6. Key deliverables — components
7. Hero scenarios
8. Scope & non-goals
9. The wedge — first beachhead
10. Timeline & maturity
11. Risks & trade-offs
12. The ask
13. Evidence & open questions

Depth lives in 4–7; the decision lives in 2, 9, and 11–12. A reader with two minutes reads 2, 9, 12 and can act.

---

## 1. Metadata & status

- **Insight it must deliver:** this is a live decision artifact with an owner and a clock — not a musing. Who wrote it, who approves, by when.
- **Style & format:** a compact header block. `Status:` (Draft / Proposal / Approved). `Target approval date:`. `Authors / Collaborators / Approver(s):` with real names. `Last modified:`.
- **Questions to answer:**
  - Who is the single accountable author (not a committee)?
  - Who has to say yes for this to proceed, by name and role?
  - What is the decision deadline, and what happens if it slips?

## 2. Bottom line (BLUF)

- **Insight it must deliver:** the identity of the product and the ask, in the first paragraph. The reader can stop here and still know what they're approving.
- **Style & format:** 3–5 sentences, no jargon. One line of *identity* ("X lets [user] do [job] without [pain]"), one line of *stakes*, one line of *ask*. Never open with background or history.
- **Questions to answer:**
  - In one sentence, who is this for and what job does it win them?
  - What are you asking the reader to approve — a decision, a spend, a headcount, a go/no-go — and by when?
  - If the reader reads only this paragraph, do they know what to do?
- **Depth trap:** "a platform that empowers everyone to do more" is not an identity. Name the user and the job.

## 3. Why now

- **Insight it must deliver:** the forcing function. Why this is urgent *this quarter*, not a perennial nice-to-have.
- **Style & format:** 2–4 lines. Tie to a trend the reader already believes (growth, cost curve, competitor move, a breaking point in the status quo). Quantify the trajectory if you can.
- **Questions to answer:**
  - What changed, or is about to, that makes waiting expensive?
  - What is the cost of doing nothing for one more year — in dollars, churn, velocity, or risk?
  - Why can't the current system absorb this with incremental fixes?

## 4. Background — assets, status quo, opportunity

- **Insight it must deliver:** the reader ends knowing *what you already hold* (unfair advantage), *what's broken* (the pain, evidenced), and *the gap between them* (the opportunity).
- **Style & format:** three short subsections. **Assets we hold** — the data/infra/position that makes this *yours* to build. **The status quo** — the pain, ideally sourced from real user interviews, with the mechanism of the pain named (e.g. "context-switching tax across N tools"). **The opportunity** — the shape of the better world, one paragraph.
- **Questions to answer:**
  - What do we uniquely have that a competitor would need years to replicate?
  - What is the pain, in the user's words — and how do we *know* it (interviews, tickets, metrics), not assume it?
  - What is the single most expensive symptom of the status quo today?
  - Why hasn't this been solved already — what made it hard?
- **Depth trap:** status quo written from the builder's chair ("our indexing is limited") instead of the user's ("support staff open five apps to close one ticket"). Lead with the human cost.

## 5. The product — identity & capabilities

- **Insight it must deliver:** what the thing *is*, expressed as a short set of capabilities a user would recognize — not an architecture.
- **Style & format:** one framing sentence, then a **numbered list of 4–6 capabilities**, each phrased as an outcome the user gets ("one search box that understands anything you type"), not a component you build. A "ten-thousand-meter view" diagram is welcome here; label it clearly as *not* an architecture.
- **Questions to answer:**
  - Can you state the product as 4–6 capabilities a non-engineer would recognize?
  - Is each capability an outcome for the user, or a box on your diagram? Rewrite any that are boxes.
  - Which one capability, if you shipped only it, would still be worth building?
- **Depth trap:** the capability catalog that grows to impress. Signal over volume — if a capability doesn't change what the user can *do*, it's an appendix item.

## 6. Key deliverables — components

- **Insight it must deliver:** for each major building block: **what it does → what pain it removes → why it's hard.** This is where technical depth earns its place.
- **Style & format:** one subsection per deliverable, named for what it does (not internal codenames). Three beats each: function, the pain/outcome it maps to, and the non-obvious constraint that makes it real engineering. Keep codenames in parentheses if you must keep them at all.
- **Questions to answer:**
  - For each component: what user-facing pain does it remove? (If none, why is it here?)
  - What makes building this *hard* — the constraint the textbook version doesn't face?
  - Which of these are table-stakes commodity, and which are the actual differentiators? Say so.
  - Whose work is each — a team you have, or a team you're asking for?
- **Depth trap:** naming components by codename and describing them by architecture. The reader buys pain removed, not modules shipped. (See Case B — commodity work claimed by category.)

## 7. Hero scenarios

- **Insight it must deliver:** proof the product is real, told as a concrete user journey end-to-end. Scenarios are where an abstract vision becomes believable.
- **Style & format:** 2–4 named scenarios, each a short narrative: a specific user, a specific goal, the steps through the product, the payoff. Use realistic inputs. Show components working *together*, not in isolation.
- **Questions to answer:**
  - For each scenario: who is the user, what did they want, and what did they get that they couldn't before?
  - Does the journey use real, plausible inputs — or toy placeholders that dodge the hard case?
  - Which scenario is the most valuable and the most reachable? (That answer is your wedge — Section 9.)
  - What breaks in this scenario today, step by step, without the product?

## 8. Scope & non-goals

- **Insight it must deliver:** the boundary. What this product is **not**, and what you are explicitly choosing not to build (yet). Absence of this section is the #1 tell of an un-costed vision.
- **Style & format:** two short lists — **In scope (first release)** and **Explicitly out of scope**. One line each, with a one-clause reason for the biggest cuts.
- **Questions to answer:**
  - What will a reasonable reader *assume* is included that isn't? Name it here.
  - What are you deliberately deferring, and what has to be true before it comes back?
  - Where does this product stop and an adjacent team's product begin?
- **Depth trap:** "any data, anywhere, understood" — unbounded scope reads as un-costed. A boundary is a sign of judgement, not timidity.

## 9. The wedge — first beachhead

- **Insight it must deliver:** the *one* scenario, user, and data source you win first — and why that one. This is the heart of the doc.
- **Style & format:** a tight half-page. Name the beachhead, the reason it's first (highest pain × most reachable), the definition of "won," and the metric that proves it.
- **Questions to answer:**
  - If you could ship for only one user doing one job next quarter, which — and why that one over the others?
  - What is the smallest version that delivers real value (not a demo)?
  - How will you *know* the wedge worked — one metric, with a target and a name who owns it?
  - What does winning the wedge unlock next?
- **Depth trap:** refusing to choose. A vision that serves everyone equally serves no one first. (This is the core of Case A.)

## 10. Timeline & maturity

- **Insight it must deliver:** a credible, phased path from wedge to full vision — with honest uncertainty later.
- **Style & format:** a **maturity ladder** per component across time (e.g. `POC → Improve → Mature`), laid out as a quarter-by-quarter table with an "enabled scenarios" column so each phase ties to user value. Mark far-out quarters `TBD` rather than fake-precise.
- **Questions to answer:**
  - Does each phase map to a scenario the user can actually do by then — or just internal milestones?
  - What is the first externally visible win, and in which quarter?
  - Where does the plan honestly become speculative, and does the doc admit it?
  - What is the rough cost/headcount per phase? (Even a range beats silence.)

## 11. Risks & trade-offs

- **Insight it must deliver:** what you're giving up and what could sink this. A director trusts a proposal that names its own downside.
- **Style & format:** a short list. Each risk: the thing that could go wrong, its likelihood/severity in plain words ("high, irreversible"), and the mitigation or the reason you're accepting it.
- **Questions to answer:**
  - What is the single most likely reason this fails?
  - What are you explicitly trading away by choosing this path over the obvious alternative?
  - What is irreversible once started, and what is the point of no return?
  - What would make you *kill* this after the POC?

## 12. The ask

- **Insight it must deliver:** the unmissable, specific decision. Spend, headcount, go/no-go, and the date.
- **Style & format:** a boxed or bolded block near the top *and* restated here. Concrete: "Approve N engineers for two quarters to ship the [wedge] POC; go/no-go review on [date]."
- **Questions to answer:**
  - Is the ask a single decision, or has it smuggled in two? (Two asks = two docs.)
  - Is every number defensible under a skeptical panel?
  - Does the reader know exactly what "yes" commits them to — and what "not yet" costs?

## 13. Evidence & open questions

- **Insight it must deliver:** the few numbers that carry the argument, sourced; and the honest list of what you don't yet know.
- **Style & format:** a compact evidence list (each figure with its source) and an open-questions list. No placeholders — a `[fill in]` either becomes a number and a name or the line is cut.
- **Questions to answer:**
  - Which 2–3 numbers actually carry the case, and who verified each?
  - What are the load-bearing assumptions, and what happens to the plan if one is wrong?
  - What do you most need the reader's input or decision on?

---

## Style rules for the whole document

1. **BLUF or it fails.** The ask and the identity are in the first paragraph. If they're not, restructure — don't add a summary at the end.
2. **One product, one wedge, one ask.** A doc with two asks is two docs.
3. **Outcomes over architecture.** Name things for what the user gets, not for the module you build or its codename. Define any unavoidable term in five words.
4. **Curate, don't inventory.** A strongest-first, cut-down set beats an exhaustive catalog. If you could keep only three capabilities, which? Demote the rest to an appendix.
5. **Every number is sourced and survives a skeptic.** No decoration metrics, no raw counts standing in for outcomes.
6. **Name the hard part before the fix.** The credit is in framing the constraint that made this non-trivial; once solved it looks obvious and the reader under-prices it.
7. **Boundaries signal judgement.** Scope and non-goals are a feature of the doc, not an admission of weakness.
8. **Ship for review early.** Get a senior reader on it before "done"; plain format, content carries.

## The one-minute self-review (fire before you send)

- Can a reader act after paragraph one? (BLUF)
- Is there exactly one ask, with a number, a name, and a date?
- Can you point to the single wedge — one user, one job, one quarter?
- Is anything explicitly out of scope?
- Does each capability change what a user can *do*?
- Is the hardest constraint named *before* its solution?
- Would every number survive a hostile panel?

If any answer is no, the doc isn't ready — and Case A is where it will fail.
