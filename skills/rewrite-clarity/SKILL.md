---
name: rewrite-clarity
description: Apply Amazon-style clear writing rules to a document. Use when the user says "rewrite for clarity", "apply writing guidelines", "clean up this doc", "remove weasel words", or wants to improve document clarity with data-driven language.
version: 0.1.0
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

### 3. Analyze for Issues

Scan the document using the loaded guidelines:

| Category         | Reference Section                                            | Priority                    |
| ---------------- | ------------------------------------------------------------ | --------------------------- |
| Weasel words     | Weasel Word Patterns + Common Offenders + Prohibited Phrases | High — must fix             |
| Verbose phrases  | Word Replacements table                                      | Medium — should fix         |
| Long sentences   | Core Principles (>30 words rule)                             | Low — consider splitting    |
| Vague adjectives | Adjectives Needing Data table                                | Low — add data if available |

### 4. Present Findings

Output a summary table with line numbers and suggestions:

```markdown
## Analysis: {filename}

| Category         | Count | Action                |
| ---------------- | ----- | --------------------- |
| Weasel words     | N     | Must fix              |
| Verbose phrases  | N     | Should fix            |
| Long sentences   | N     | Consider splitting    |
| Vague adjectives | N     | Add data if available |

### Weasel Words Found
| Line | Text | Suggestion |
| ---- | ---- | ---------- |
| ...  | ...  | ...        |

### Verbose Phrases Found
| Line | Text | Replacement |
| ---- | ---- | ----------- |
| ...  | ...  | ...         |
```

### 5. Offer Actions

1. **Apply safe fixes** — Auto-replace verbose phrases (deterministic, always correct)
2. **Show diff preview** — Preview all suggested changes
3. **Interactive mode** — Fix issues one by one with user input for data
4. **Export issues** — Save as TODO list in same directory

### 6. Apply Changes (If Requested)

For **safe fixes**: apply all verbose phrase replacements from Word Replacements table using Edit tool.

For **interactive mode**: present each weasel word/adjective, ask user for the actual data, apply change.

## Rules

1. **Never invent data** — Ask the user for actual figures when replacing vague terms
2. **Preserve meaning** — Verbose replacements must be semantically equivalent
3. **Respect context** — Some hedge words are appropriate (uncertainty is real); flag but don't auto-replace
4. **One pass** — Don't re-analyze after changes; user can re-run if needed
