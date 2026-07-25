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

### 1. Dry-run against the transcript

```bash
python3 .claude/commands/lint-transcript-normalise/scripts/normalise_transcript.py \
    "raw/.../transcript.md"
```

This prints two sections and writes **nothing**:

- **Confident replacements (would apply)** — safe garble → correct-name fixes.
- **Entities to confirm** — each ambiguous hit with `Lnn`, the suggested entity + its
  wikilink, and the full line for context.

### 2. Confirm the ambiguous mentions with the user

Present the **"Entities to confirm"** list to the user. For each line, they decide:
this is entity X / this is someone else / leave it. Do **not** guess. Common judgment
calls: Is `Mac` the person Mark, or "Mac UI"?

### 3. Apply confident fixes

Once the confident list looks right, write them in place:

```bash
python3 .claude/commands/lint-transcript-normalise/scripts/normalise_transcript.py \
    "raw/.../transcript.md" --write
```

### 4. Apply confirmed ambiguous fixes by hand

For each ambiguous mention the user confirmed, fix that specific occurrence with the
Edit tool (targeted, line-by-line — never a blanket replace of a single letter or
common word). Leave unconfirmed ones as-is.

### 5. Grow the dictionary

When the user confirms a **new** mapping (a garble not yet in the dictionary, or a new
entity), add it to `config/corrections.json`:

- Put genuine, distinctive, unambiguous garbles under `variants`.
- Put anything risky (single letters, real words, shared first names, cross-entity
  collisions) under `ambiguous_variants`.
- Resolve the `wikilink` against `wiki/**/members/`, `raw/People/**`,
  and `wiki/portal.md`; reuse the **exact** existing slug/display. Never invent a slug.
- Never seed a common English word (e.g. `you`, `the`) as any kind of variant.

### 6. Hand off to ingest

The transcript now has corrected plain-text names and a confirmed set of mentions.
Run `/second-brain-ingest` — its step 1b now only has to link the resolved names,
not resolve them from scratch.

## Dictionary Schema

```json
{
  "version": 1,
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

## Matching Rules (implemented by the script)

- Confident `variants`: **case-insensitive**, whole-word, and never applied inside an
  existing `[[wikilink]]` span (those are masked first).
- Ambiguous `variants`: **case-sensitive**, whole-word — keeps a single letter like
  `G` from matching every stray lowercase `g`.
- The script is a **report + spelling fixer**, never a gate: it always exits 0.

## Rule

A wrong `[[name]]` is worse than an unlinked plain-text mention flagged for review.
When in doubt, leave it in `ambiguous_variants` and ask.
