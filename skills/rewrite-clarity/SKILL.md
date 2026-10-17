---
name: rewrite-clarity
description: Apply Amazon-style clear writing rules to a document, and presentation-clarity rules (legible / simple / obvious, concrete one-liners, claim titles, honest numbers, slide density) to pitch decks and product presentations. Use when the user says "rewrite for clarity", "apply writing guidelines", "clean up this doc", "remove weasel words", "clean up these slides / this deck", "remove marketing fluff", or wants to improve document or presentation clarity with data-driven language.
version: 0.3.0
---

# Rewrite for Clarity

Apply `references/writing-communication.md` guidelines to improve document clarity. Based on Amazon's "Write Like an Amazonian" principles. For pitches, product presentations and exec decks, also apply `references/presentation-clarity.md` (YC deck-design rules: legible, simple, obvious).

## Input

Accepts one of:
- A file path as argument: `/rewrite-clear path/to/document.md`
- No argument: apply to the file currently being discussed

## Workflow

### 1. Load Guidelines

Read `references/writing-communication.md` to get:
- **Weasel word patterns** — from "Weasel Word Patterns" table
- **Common offenders** — from "Common Offenders" table
- **Prohibited phrases** — from "Prohibited Phrases" list
- **Word replacements** — from "Word Replacements" table (21 entries)
- **Adjectives needing data** — from "Adjectives Needing Data" table
- **Red flags** — from "Red Flags in Writing" section

Then read `references/presentation-clarity.md` to get:
- **Marketing language** — from "Marketing Language" table
- **Jargon by audience** — from "Jargon by Audience" section
- **One-liner tests** — from "One-Liner Tests" table
- **Claim titles** — from "Claim Titles" table
- **Number presentation** — from "Number Presentation" table
- **Slide density** — from "Slide Density Rules" table (deck mode only)

### 1b. Detect Document Type

- **Doc mode** (default) — prose: memo, proposal, wiki page, email.
- **Deck mode** — a slide outline or exported deck: markdown with `---` slide separators or `## Slide N` headings, a `.pptx`/`.key` text export, or the user says "deck", "slides", "pitch", "presentation".

Themes marked *(deck)* in the registry only run in deck mode. If the document doesn't state its **audience** (customer vs investor / exec / cross-functional), ask once — it decides whether industry jargon is a finding.

### 2. Read the Target Document

Read the target file completely.

### 3. Analyze by Theme

Scan the document one theme at a time. Each theme is a self-contained unit defined in the **Theme Registry** below. Produce a separate findings block per theme so results stay organized and each theme can be acted on independently.

#### Theme Registry

Each theme declares: its reference section, its **fix mode**, and its priority. The fix mode determines what happens in steps 5–6:

- **auto** — deterministic 1:1 replacement, always correct, no user input needed → applied automatically in step 5
- **assisted** — requires user-supplied data or a judgment call → offered as an option in step 6

| Theme            | Reference Section                                            | Fix Mode | Priority | User Effort            |
| ---------------- | ------------------------------------------------------------ | -------- | -------- | ---------------------- |
| Verbose phrases  | Word Replacements table                                      | auto     | Medium   | none                   |
| Weasel words     | Weasel Word Patterns + Common Offenders + Prohibited Phrases | assisted | High     | high (needs data)      |
| Vague adjectives | Adjectives Needing Data table                                | assisted | Low      | high (needs data)      |
| Long sentences   | Core Principles (>30 words rule)                             | assisted | Low      | medium (needs rewrite) |
| Marketing language | presentation-clarity: Marketing Language                   | assisted | High     | medium (needs mechanism) |
| Abstract one-liner | presentation-clarity: One-Liner Tests (title, subtitle, first sentence) | assisted | High | medium (needs mechanism) |
| Undefined acronyms & jargon | writing-communication: Acronym Handling + presentation-clarity: Jargon by Audience | assisted | Medium | low (needs definition) |
| Unclear numbers  | presentation-clarity: Number Presentation (undefined, cumulative, double-axis, uncaptioned) | assisted | Medium | high (needs data) |
| Topic titles *(deck)* | presentation-clarity: Claim Titles                      | assisted | Medium   | medium (needs cut/split) |
| Slide density *(deck)* | presentation-clarity: Slide Density Rules (bullets, words, screenshots, diagrams, animation) | assisted | Medium | medium (needs cut/split) |

> **Extending:** to add a theme, append a row here with its reference section, fix mode, priority, and user-effort estimate. `auto` themes flow into step 5; `assisted` themes flow into step 6. No other part of the workflow changes.

For each theme in the registry, scan the document and collect findings with line numbers.

### 4. Present Findings

Output a summary table, then one findings block per theme (only for themes with hits):

```markdown
## Analysis: {filename}

| Theme            | Count | Fix Mode | Priority |
| ---------------- | ----- | -------- | -------- |
| Verbose phrases  | N     | auto     | Medium   |
| Weasel words     | N     | assisted | High     |
| Vague adjectives | N     | assisted | Low      |
| Long sentences   | N     | assisted | Low      |
| Marketing language | N   | assisted | High     |
| …                | N     | …        | …        |

### Verbose phrases (auto)
| Line | Text | Replacement |
| ---- | ---- | ----------- |
| ...  | ...  | ...         |

### Weasel words (assisted)
| Line | Text | What's needed |
| ---- | ---- | ------------- |
| ...  | ...  | ...           |
```

### 5. Apply Auto Fixes By Default

Apply every finding from **auto** fix-mode themes directly with the Edit tool **by default** — do **not** ask first. These are deterministic replacements (e.g. verbose phrase swaps) that are always correct. The only exception: if the user has explicitly asked to preview or approve changes first, hold and show the diff instead.

After applying, report what was changed in one line per theme (e.g. "Verbose phrases: applied 7 replacements").

### 6. Offer Assisted Fixes, Grouped by User Effort

For **assisted** fix-mode themes, present the remaining work as options ordered by how much effort each requires from the user — lowest effort first — so they can pick what they have time for. Use the AskUserQuestion tool with options (if available) such as:

- **Quick wins** — assisted fixes where the needed input is small or you can infer a strong candidate for the user to confirm
- **Needs data** — weasel words / vague adjectives requiring the user to supply actual metrics
- **Needs rewrite** — long sentences requiring the user to split or restructure
- **Needs mechanism** — marketing language and abstract one-liners: the user describes what actually happens (who does what, with what result)
- **Needs cut/split** *(deck)* — topic titles to turn into claims, dense slides to split or move to the appendix
- **Skip** — leave assisted findings as-is

For whichever the user picks :

1. **Show diff preview** — Preview all suggested changes by effort bucket
2. **Interactive mode** — walk through those findings, collect the required input & propose fixes one by one with input
3. **Apply or Export issues** — If satisfy user can apply OR save all remaining TODO list in same directory (if the user doesn't have time)

Never invent data.
## Rules

1. **Never invent data** — Ask the user for actual figures when replacing vague terms (assisted themes)
2. **Preserve meaning** — Auto replacements must be semantically equivalent
3. **Respect context** — Some hedge words are appropriate (uncertainty is real); classify these as assisted, never auto-replace
4. **Auto vs assisted is the gate** — Only `auto` fix-mode themes apply without asking; every `assisted` theme waits for the user's choice in step 6
5. **One pass** — Don't re-analyze after changes; user can re-run if needed
6. **Audience decides jargon** — industry jargon is fine for a customer audience; flag it for investor / exec / cross-functional readers
7. **Clarity, not substance** — if a slide's *argument* is weak (wrong audience, no evidence, missing ask), note it once and hand off to `review-product-strategy` (pitch checks P1–P12) or `review-engineering-director`; don't critique strategy here
