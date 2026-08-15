---
name: rewrite-clarity
description: Apply Amazon-style clear writing rules to a document. Use when the user says "rewrite for clarity", "apply writing guidelines", "clean up this doc", "remove weasel words", or wants to improve document clarity with data-driven language.
version: 0.2.0
---

# Rewrite for Clarity

Apply `references/writing-communication.md` guidelines to improve document clarity. Based on Amazon's "Write Like an Amazonian" principles.

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

For **assisted** fix-mode themes, present the remaining work as options ordered by how much effort each requires from the user — lowest effort first — so they can pick what they have time for. Use the AskUserQuestion tool with options such as:

- **Quick wins** — assisted fixes where the needed input is small or you can infer a strong candidate for the user to confirm
- **Needs data** — weasel words / vague adjectives requiring the user to supply actual metrics
- **Needs rewrite** — long sentences requiring the user to split or restructure
- **Skip** — leave assisted findings as-is

For whichever the user picks, walk through those findings, collect the required input, and apply. Never invent data.

## Rules

1. **Never invent data** — Ask the user for actual figures when replacing vague terms (assisted themes)
2. **Preserve meaning** — Auto replacements must be semantically equivalent
3. **Respect context** — Some hedge words are appropriate (uncertainty is real); classify these as assisted, never auto-replace
4. **Auto vs assisted is the gate** — Only `auto` fix-mode themes apply without asking; every `assisted` theme waits for the user's choice in step 6
5. **One pass** — Don't re-analyze after changes; user can re-run if needed
