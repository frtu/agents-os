---
concept: extensible-dictionary
summary: Move growing lookup data (word replacements, mappings, allow/deny lists) out of SKILL.md into a version-controlled JSON config that a script reads and the agent grows after every user confirmation.
exemplars: [lint-transcript-normalise]
related: [case-studies]
---

# Extensible dictionary

## Problem

A skill's knowledge is mostly **data**, not process: a list of word replacements, name corrections, synonym maps, thresholds. When that data lives in `SKILL.md`:

- `SKILL.md` gets edited for every new word, so the process document churns while the process itself never changes.
- The list grows until it crowds out the instructions and costs tokens on every run.
- The agent applies entries by "reading and remembering" instead of deterministically, so matches are inconsistent.
- A user answers the same question twice ("is `Flint` Flink?") because nothing persisted the answer.

## Pattern

Split the skill into a **stable process** and a **growing dictionary**. The dictionary is a JSON file under `config/`, with a self-describing schema. A stdlib script in `scripts/` reads it and applies it deterministically. `SKILL.md` describes the process, the schema and the **write-back rule**: every user confirmation becomes a dictionary entry in the same turn. New vocabulary then grows by editing JSON only; `SKILL.md` changes only when the process or schema changes.

```text
skill-name/
├── SKILL.md                  # Process + schema + write-back rule. Never lists entries.
├── config/
│   └── {dictionary}.json     # version, rules (field docs), entries; grows over time
└── scripts/
    ├── {apply}.py            # Reads the JSON, applies/flags matches, prints a report
    └── test_{apply}.py       # Fixture dictionary + fixture input → expected report
```

## Use when / Don't use when

**Use when**

- The skill maps inputs to outputs through a list that **grows with use** (corrections, aliases, glossary, routing table, deny-list).
- Matching can be expressed as **rules** (whole word, case-sensitivity, scope) a script can apply the same way every time.
- Users confirm new entries during normal runs, so the data is discovered, not designed up front.

**Don't use when**

- The "entries" are judgement-heavy examples that need prose, context and a narrative → use [case-studies](./case-studies.md).
- The list is short and closed (3–5 fixed values that won't grow) → keep it inline in `SKILL.md`.
- The data is someone else's source of truth (the vault's member pages, a team roster) → point to it; don't copy it into a dictionary.

## Anatomy

| Part | Rule |
| ---- | ---- |
| **`version`** | Integer. Bump on **schema** change only, never on each new entry. |
| **`description` + `rules`** | The JSON documents itself: one line per field saying what it means and how it is matched. An agent editing the file without reading `SKILL.md` still writes valid entries. |
| **Confidence tiers** | Separate entries the script may **auto-apply** (distinctive, unambiguous) from entries it may only **flag** for a human (short, real words, collisions). One tier per field, never a boolean per entry the script must interpret. |
| **Negative list** | A top-level list of tokens confirmed to mean *nothing* (e.g. `known_noise`), so the agent's manual sweep stops re-asking. Only confirmed dead ends go here; merely unresolved items stay out so they surface again. |
| **Canonical target** | Each entry names its one correct output (and, if relevant, its link target). Never list the target as its own variant. Resolve link targets against the existing source; never invent one. |
| **Script** | Stdlib only; default path resolves the config relative to the script (`Path(__file__).parent.parent / "config" / …`) with a `--config`-style override. Dry-run by default; prints a report; exits 0 (report tool, not a gate) unless the skill is explicitly a gate. |
| **Write-back rule** (in `SKILL.md`) | Each user confirmation → one dictionary write, in the same turn, without asking. A table maps *what the user said* → *which field to write*. Then tell the user, one line per entry, so growth stays visible and correctable. |
| **Silence caveat** (in `SKILL.md`) | The script only knows listed entries. An empty report is not a clean bill of health, so `SKILL.md` adds a manual sweep for unlisted candidates and merges them into one list the user answers once. |

## Exemplar walkthrough — `lint-transcript-normalise`

Normalises garbled proper nouns in Whisper/Zoom transcripts before ingest.

| Part | Where it lives |
| ---- | -------------- |
| Dictionary | `lint-transcript-normalise/config/corrections.json` — `version`, `description`, `rules` (one doc line per field), `known_noise`, `corrections[]` |
| Confidence tiers | `variants` (case-insensitive, auto-fixed) vs `ambiguous_variants` (case-sensitive, flag only) |
| Negative list | top-level `known_noise` — ignored by the script, read by the manual sweep |
| Canonical target | `correct` (plain-text spelling) + `wikilink` (resolved `[[slug\|Display]]`, empty if no page exists) |
| Script | `lint-transcript-normalise/scripts/normalise_transcript.py` — default config resolved next to the script, `--corrections` override, dry run by default, masks existing `[[…]]` spans, always exits 0 |
| Write-back rule | `SKILL.md` → *5. Grow the dictionary — every time, without being asked*: the user-said → write table (new variant / ambiguous token / dead end) |
| Silence caveat | `SKILL.md` → *2. Confirm the ambiguous mentions* → "The dictionary is not the whole picture" |
| Schema in `SKILL.md` | `SKILL.md` → *Dictionary Schema* + *Matching Rules*: the contract, not the entries |

**Why it succeeds:** every change to its `SKILL.md` so far has been a process or schema change; no entry has ever been added there. The ship-empty `corrections: []` makes the skill generic; each vault grows its own entries. The two tiers keep risky tokens (single letters, shared first names) from being silently rewritten, which is the failure that matters most in that domain: *a wrong name is worse than an unlinked one*.

**Gap to avoid copying:** the script has no `test_normalise_transcript.py` yet. A new skill using this pattern should ship the test with a fixture dictionary (see README → *Folder layout*).

## Adoption checklist

1. **Find the data.** List everything in the skill (or the planned skill) that is a lookup: replacements, aliases, thresholds, routing. If it will grow, it moves out.
2. **Design the schema first.** Fields, the confidence tiers, the negative list, the canonical target. Write the `rules` block in the JSON before any entry.
3. **Ship it empty or with synthetic entries.** Real names, team terms and internal systems belong to the user's copy, not the template (AGENTS.md step 5 *Keep generic and specific apart*).
4. **Write the script** with the matching rules from the schema, a dry-run default, a config override and a report output. Add `test_{script}.py` with a fixture dictionary.
5. **Rewrite `SKILL.md`** to describe the process, the schema and matching rules, the write-back table and the silence caveat. Remove every inline entry.
6. **Verify:** add one entry to the JSON only, run the script, and confirm the new behaviour appears with no `SKILL.md` change.

## Anti-patterns

- **Entries in `SKILL.md`.** Any inline list "for convenience" becomes the second source of truth and drifts from the JSON.
- **One tier for everything.** Auto-applying short or common tokens corrupts the output silently. Uncertain entries must default to *flag*.
- **Seeding common words** (`you`, `the`, `app`) as variants — they match everywhere.
- **Deferred write-back.** "I'll add it later" means the same question next run. The write happens in the same turn as the confirmation.
- **Inventing targets.** A link or canonical form that doesn't exist in the source of truth creates a broken or wrong reference that looks authoritative.
- **Version bump per entry.** Makes the version meaningless for detecting schema changes.
- **Treating an empty report as "clean".** The script is only as good as its dictionary; keep the manual sweep.
