---
name: lint-transcript-normalise
description: Pre-ingest clean-up for auto-generated transcripts (Whisper/Zoom/xx). Resolves garbled proper nouns against a JSON correction dictionary BEFORE ingest so wrong names never become wikilinks. Use when the user adds a transcript to raw/ and says "normalise this transcript", "clean up the names", or right before /second-brain-ingest on any transcript source.
version: 0.1.0
allowed-tools: Bash Read Write Edit
---

# Transcript Normalise (lint)

Auto-generated transcripts are **unreliable for proper nouns**. This skill is the
**pre-ingest** step that fixes them, so ingestion skill never has to guess a
name and never promotes a transcription artifact into a `[[wikilink]]`.

It is driven by a JSON dictionary that maps each canonical entity ("proper output")
to its list of transcription errors, split into two confidence tiers:

- **variants** — distinctive garbles that are safe to auto-fix to the correct plain
  name (e.g. `Fredo`/`Freddy`/`Fred` → `Frederic T`).
- **ambiguous_variants** — risky tokens (single letters, real words, shared first
  names) that are **only flagged** for a human to confirm, never auto-replaced.

The tool fixes **spelling only**. It does **not** inject `[[wikilinks]]` into the raw
source — linking stays the ingest step's job. The report surfaces the wikilink target
so the reviewer / ingest can link confirmed mentions.

## The Two Failure Modes This Guards Against

- **Phonetic mangling** — A lone initial or an out-of-place common word is
  a red flag, not a fact.
- **Speaker collapse** — every line may be labelled with one speaker (often the host).
  Do **not** assert who said what based on these labels.

## Files

| Path | Purpose |
| ---- | ------- |
| `config/corrections.json` | The correction dictionary (canonical entity ↔ variants ↔ ambiguous_variants ↔ wikilink). Version-controlled and grown over time. |
| `scripts/normalise_transcript.py` | Applies confident fixes and reports ambiguous mentions. Stdlib only. |

## Procedure

### 1. Run the report against the transcript

```bash
python3 .claude/commands/lint-transcript-normalise/scripts/normalise_transcript.py \
    "raw/.../transcript.md"
```

This prints two sections and writes **nothing**:

- **Confident replacements (would apply)** — safe garble → correct-name fixes.
- **Entities to confirm** — each ambiguous hit with `Lnn`, the suggested entity + its
  wikilink, and the full line for context.

### 2. Confirm the ambiguous mentions with the user

Present the **"Entities to confirm"** list to the user. For each candidate, they decide:
this is entity X / this is someone else / leave it. Do **not** guess. Common judgment
calls: Is `Mac` the person Mark, or "Mac UI"?

**Always pass the sentences the term was used in.** A bare list of tokens is not
answerable — the user cannot resolve `Julie` without seeing that the line reads
*"Julie, we can… I can discuss with Zolly."* For each candidate, quote **every**
occurrence as `Lnn: "<full sentence>"` (cap at ~5 lines, then say "+N more"). The
sentence is the evidence; the token alone is not.

**The dictionary is not the whole picture.** The script only flags tokens already listed
under `ambiguous_variants`, so a garble for an entity that isn't in `corrections.json`
yet produces **no output at all** — silence from the script is not a clean bill of
health. After the dry-run, read the transcript yourself and add to the confirm list any:

- name-shaped token that resolves to nothing in `wiki/**/members/`, `raw/People/**`, or `wiki/portal.md`
- lone initial or one-letter "name"
- near-miss of a known entity (`Flint`/`Flick` → Flink, `Chain Data Capture` → Change Data Capture)
- product/system/team name that appears once and matches nothing

Merge these with the script's hits into a single list so the user answers once.

### 3. Carry the resolutions forward — do not edit the transcript

There is no "apply" step. The raw transcript keeps its garbles; the **report plus the
user's confirmations** are what ingest consumes. Hold on to, and hand to ingest:

- the confident `variant → correct` map (so ingest writes `Flink`, never `Flint`)
- each confirmed ambiguous occurrence as `Lnn → entity` (resolves *that* line only)
- the tokens the user declined to resolve — these stay **plain text**, never a wikilink

The reason not to rewrite the source: a corrected transcript silently loses the evidence
of what the recording actually said, and a wrong "correction" then becomes unfalsifiable.
Correct at the wiki-page boundary instead, where a `> **Caveat:**` note can travel with it.

### 5. Grow the dictionary — every time, without being asked

**Every user confirmation is a dictionary write.** The moment the user resolves a
mention, update `config/corrections.json` in the same turn. Do not defer it, do not
batch it to "later", and do not ask permission — the whole point of the dictionary is
that the same garble is never asked about twice. A confirmation that isn't persisted is
a question you will ask again next transcript.

Three cases, all of which write:

| The user said | Write |
| ------------- | ----- |
| "`Flint` is Flink" — garble not in the dictionary | New `variants` entry (or a new `corrections` entry if the entity is new) |
| "`Julie` here is Zolly" — risky token, this occurrence resolved | Add the token to that entity's `ambiguous_variants` so it keeps being flagged, and record the resolution in `note` |
| "`Baba` is nobody / leave it" — dead end | Add to the top-level `known_noise` list so the step-2 manual sweep stops re-surfacing it |

Field rules when writing:

- Put genuine, distinctive, unambiguous garbles under `variants`.
- Put anything risky (single letters, real words, shared first names, cross-entity
  collisions) under `ambiguous_variants` — a confirmation resolves *this occurrence*,
  it does not make the token globally safe to auto-replace.
- Resolve the `wikilink` against `wiki/**/members/`, `raw/People/**`,
  and `wiki/portal.md`; reuse the **exact** existing slug/display. Never invent a slug.
- Never seed a common English word (e.g. `you`, `the`) as any kind of variant.
- Bump `version` when the schema changes, not on every entry.

Then tell the user what you added, in one line per entry, so the dictionary's growth is
visible and correctable.

### 6. Hand off to ingest

The transcript now has corrected plain-text names and a confirmed set of mentions.
Run `/second-brain-ingest` — its step 1b now only has to link the resolved names,
not resolve them from scratch.

## Dictionary Schema

```json
{
  "version": 1,
  "known_noise": ["Toto"],
  "corrections": [
    {
      "correct": "Frederic T",
      "type": "person",
      "wikilink": "[[fred-t|Frederic T]]",
      "variants": [],
      "ambiguous_variants": ["Fredo", "Freddy"],
      "note": "Manager"
    }
  ]
}
```

| Field | Rule |
| ----- | ---- |
| `correct` | Canonical plain-text spelling. Confident fixes rewrite variants to this. Never list the correct spelling as a variant. |
| `variants` | Case-insensitive, whole-word, auto-replaced. Must be distinctive, non-word, single-entity. |
| `ambiguous_variants` | Case-sensitive, whole-word, **flag only**. Single letters, real words, shared names. |
| `wikilink` | Exact resolved `[[slug\|Display]]`. Reuse existing; never invent. |
| `type` | `person` / `product` / `system` / `team` — informational. |
| `note` | Free text. Record confirmed-but-not-auto-replaceable resolutions here. |
| `known_noise` | Top-level list of name-shaped tokens confirmed to mean nobody. The script ignores this key; it exists so the step-2 manual sweep doesn't re-ask. |

## Matching Rules (implemented by the script)

- Confident `variants`: **case-insensitive**, whole-word, and never applied inside an
  existing `[[wikilink]]` span (those are masked first).
- Ambiguous `variants`: **case-sensitive**, whole-word — keeps a single letter like
  `G` from matching every stray lowercase `g`.
- The script is a **report + spelling fixer**, never a gate: it always exits 0.

## Rule

A wrong `[[name]]` is worse than an unlinked plain-text mention flagged for review.
When in doubt, leave it in `ambiguous_variants` and ask.
