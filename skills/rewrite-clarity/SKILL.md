---
name: rewrite-clarity
description: Apply Amazon-style clear writing rules to a document, presentation-clarity rules (legible / simple / obvious, concrete one-liners, claim titles, honest numbers, slide density) to pitch decks and product presentations, and engagement-clarity rules (hook, takeaway, action, honest urgency) to announcements and invites. Use when the user says "rewrite for clarity", "apply writing guidelines", "clean up this doc", "remove weasel words", "clean up these slides / this deck", "remove marketing fluff", "make this announcement / invite engaging", or wants to improve document, presentation or announcement clarity.
version: 0.5.0
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
- **Word replacements** — not read here: they live in `config/word-replacements.json` and are applied by `scripts/replace_words.py` (see *Verbose phrases dictionary*)
- **Adjectives needing data** — from "Adjectives Needing Data" table
- **Red flags** — from "Red Flags in Writing" section

Then read `references/presentation-clarity.md` to get:
- **Marketing language** — from "Marketing Language" table
- **Jargon by audience** — from "Jargon by Audience" section
- **One-liner tests** — from "One-Liner Tests" table
- **Claim titles** — from "Claim Titles" table
- **Number presentation** — from "Number Presentation" table
- **Slide density** — from "Slide Density Rules" table (deck mode only)

For announcements and invites, read `references/engagement-clarity.md` to get:
- **Engagement patterns** — from "Engagement Patterns" table
- **Expectation-not-spoiler rule** — from "Set Expectations, Don't Spoil"
- **Honest urgency** — from "Honest Urgency" table
- **Announcement density** — from "Announcement Density" section

### 1b. Detect Document Type

- **Doc mode** (default) — prose: memo, proposal, wiki page, email.
- **Deck mode** — a slide outline or exported deck: markdown with `---` slide separators or `## Slide N` headings, a `.pptx`/`.key` text export, or the user says "deck", "slides", "pitch", "presentation".
- **Announcement mode** — an invite or broadcast read in <1 minute: event announcement, meeting invite, FYI broadcast. Trigger: user says "announcement", "invite", "broadcast", or the doc is an event notice with time + place + audience.

Announcement mode adds the engagement themes to the scan; doc and deck themes still apply where they hit.

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
| Verbose phrases  | `config/word-replacements.json` via `scripts/replace_words.py` (`replacements` tier; `suggestions` tier → Quick wins) | auto     | Medium   | none                   |
| Weasel words     | Weasel Word Patterns + Common Offenders + Prohibited Phrases | assisted | High     | high (needs data)      |
| Vague adjectives | Adjectives Needing Data table                                | assisted | Low      | high (needs data)      |
| Long sentences   | Core Principles (>30 words rule)                             | assisted | Low      | medium (needs rewrite) |
| Marketing language | presentation-clarity: Marketing Language                   | assisted | High     | medium (needs mechanism) |
| Abstract one-liner | presentation-clarity: One-Liner Tests (title, subtitle, first sentence) | assisted | High | medium (needs mechanism) |
| Undefined acronyms & jargon | writing-communication: Acronym Handling + presentation-clarity: Jargon by Audience | assisted | Medium | low (needs definition) |
| Unclear numbers  | presentation-clarity: Number Presentation (undefined, cumulative, double-axis, uncaptioned) | assisted | Medium | high (needs data) |
| Topic titles *(deck)* | presentation-clarity: Claim Titles                      | assisted | Medium   | medium (needs cut/split) |
| Slide density *(deck)* | presentation-clarity: Slide Density Rules (bullets, words, screenshots, diagrams, animation) | assisted | Medium | medium (needs cut/split) |
| Buried hook *(announcement)* | engagement-clarity: Engagement Patterns (hook position, takeaway, action) | assisted | Medium | medium (needs hook) |
| Topic headers *(announcement)* | engagement-clarity: Engagement Patterns (takeaway headers) | auto     | Low      | none                   |
| Missing/unsupported action *(announcement)* | engagement-clarity: Engagement Patterns (action, excuse removal, honest urgency) | assisted | High | low (needs confirmation) |
| Spoiler teaser *(announcement)* | engagement-clarity: Expectation-not-Spoiler | assisted | High | low (curiosity gap is a rewrite) |

> **Extending:** to add a theme, append a row here with its reference section, fix mode, priority, and user-effort estimate. `auto` themes flow into step 5; `assisted` themes flow into step 6. No other part of the workflow changes.

For each theme in the registry, scan the document and collect findings with line numbers.

**Verbose phrases come from the script, not from reading.** Run the dry run and use its report as the theme's findings:

```bash
python3 <skills-dir>/rewrite-clarity/scripts/replace_words.py "{file}"
```

`Lnn: 'x' -> 'y'` lines are the auto findings; `(review)` lines go to step 6 as **Quick wins**. While scanning the other themes, also note any **verbose phrase the dictionary doesn't know yet** (e.g. "in light of the fact that") as a *New verbose phrases* finding — never apply it in step 5; it waits for the user in step 6.

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

Apply every finding from **auto** fix-mode themes directly **by default** — do **not** ask first. These are deterministic replacements that are always correct. For verbose phrases, run the script with `--write` (same command as step 3); for other auto themes, edit the file. The only exception: if the user has explicitly asked to preview or approve changes first, hold and show the diff instead.

After applying, report what was changed in one line per theme (e.g. "Verbose phrases: applied 7 replacements").

### 6. Offer Assisted Fixes, Grouped by User Effort

For **assisted** fix-mode themes, present the remaining work as options ordered by how much effort each requires from the user — lowest effort first — so they can pick what they have time for. Use the AskUserQuestion tool with options (if available) such as:

- **Quick wins** — assisted fixes where the needed input is small or you can infer a strong candidate for the user to confirm (incl. the dictionary's `(review)` hits and *New verbose phrases*)
- **Needs data** — weasel words / vague adjectives requiring the user to supply actual metrics
- **Needs rewrite** — long sentences requiring the user to split or restructure
- **Needs mechanism** — marketing language and abstract one-liners: the user describes what actually happens (who does what, with what result)
- **Needs cut/split** *(deck)* — topic titles to turn into claims, dense slides to split or move to the appendix
- **Needs hook** *(announcement)* — hook question to write, takeaway headers, CTA to confirm (date/place/agenda taken from the doc, never invented)
- **Skip** — leave assisted findings as-is

For whichever the user picks :

1. **Show diff preview** — Preview all suggested changes by effort bucket
2. **Interactive mode** — walk through those findings, collect the required input & propose fixes one by one with input
3. **Apply or Export issues** — If satisfy user can apply OR save all remaining TODO list in same directory (if the user doesn't have time)

Never invent data.

### 7. Grow the dictionary — every confirmation, without being asked

The shipped dictionary is the committed default; this step is the optional layer that extends it. When the user resolves a verbose-phrase finding, write it to `config/word-replacements.json` **in the same turn**:

| The user said                                                                  | Write                                                            |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| "yes, `in light of the fact that` → `because`" and it is equivalent everywhere | New entry in `replacements`                                      |
| "yes here", but the swap breaks in other contexts (gerund, noun, tense)        | New entry in `suggestions`, with a `note` saying where it breaks |
| "no, keep it"                                                                  | Add the phrase to `keep` so the sweep stops proposing it         |
| A `(review)` hit turns out always safe / an auto entry broke a sentence        | Move the entry between tiers and say why in `note`               |

Rules: lower-case `verbose`, no duplicate across tiers, never a single common word, bump `version` only on schema change. Then tell the user one line per entry. Run the script's tests after editing (`python3 -m unittest test_replace_words` in `scripts/`; one test validates the shipped JSON). The JSON is version-controlled: stage it with the document via `/change-management-1-stage` if the user wants changes captured.

## Verbose phrases dictionary — without an agent

`scripts/replace_words.py` applies the dictionary on its own (shell, batch, CI): files, folders (`*.md`) or stdin; dry run by default, `--write` in place, `--config FILE` for another dictionary. Without an agent the dictionary is **used, never grown**: only the `replacements` tier is applied, `suggestions` are reported, unknown phrases pass through. It skips code blocks, inline code, `[[wikilinks]]`, link targets and URLs, and keeps the match's capitalisation.

```bash
python3 <skills-dir>/rewrite-clarity/scripts/replace_words.py docs/ --write
python3 <skills-dir>/rewrite-clarity/scripts/replace_words.py - < draft.md > clean.md
```

## Rules

1. **Never invent data** — Ask the user for actual figures when replacing vague terms (assisted themes)
2. **Preserve meaning** — Auto replacements must be semantically equivalent; anything that breaks in some context goes to the `suggestions` tier
3. **Respect context** — Some hedge words are appropriate (uncertainty is real); classify these as assisted, never auto-replace
4. **Auto vs assisted is the gate** — Only `auto` fix-mode themes apply without asking; every `assisted` theme waits for the user's choice in step 6
5. **One pass** — Don't re-analyze after changes; user can re-run if needed
6. **Audience decides jargon** — industry jargon is fine for a customer audience; flag it for investor / exec / cross-functional readers
7. **Clarity, not substance** — if a slide's *argument* is weak (wrong audience, no evidence, missing ask), note it once and hand off to `review-product-strategy` (pitch checks P1–P12, teaser check P13) or `review-engineering-director`; don't critique strategy here
