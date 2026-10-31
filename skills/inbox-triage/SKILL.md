---
name: inbox-triage
description: >
  Check workspace vaults for transcripts and report which origin-vault
  transcripts have been copied to a destination vault. Scans the root folder
  (default to be configured in `./config/config.md` and `.env`), treats `global-inbox`
  as the origin vault, and every other folder as a target vault. Produces an
  origin→target table (only the sub-path after raw/transcripts) and proposes
  cp commands for files not copied yet. Use when the user says "check my
  inbox", "which transcripts are not copied", "transcript inbox status",
  "sync transcripts", or drops you in a workspace root and asks what still
  needs filing. Differs from lint-transcript-normalise (cleans names inside a
  transcript) and second-brain-ingest (turns a transcript into wiki pages) —
  this skill only reports and proposes the copy, never edits or ingests.
version: 0.1.0
allowed-tools: Bash Read Glob Grep
---

# Inbox — transcript copy status across vaults

Each workspace vault keeps raw transcripts under `raw/transcripts/**`. New
transcripts land in the origin vault (`global-inbox`); the user later copies
them into topical target vaults (infra, management, …), optionally
into sub-folders. This skill reports what has been filed where, and proposes
the copies still missing.

## Files

| Path | When to load |
| --- | --- |
| `scripts/scan_inbox.py` | Always — does the whole scan. `--json` for machine output, `--copy-cmds` to also print skeleton cp commands. |
| `config/config.md` | Only when the user wants a different root, origin vault, or vault layout. |

## Procedure

### 1. Run the scan

```bash
python3 {skills_dir}/inbox-triage/scripts/scan_inbox.py [root] [--origin global-inbox]
```

- Positional `root` defaults to be configured in `./config/config.md`; the
  `WORKSPACES_ROOT` env var overrides it; the parameter wins over the env var.
- `--origin` renames the origin vault (default `global-inbox`).
- The script matches by **filename** with the leading date stamp, case, `-`/`_`
  and spacing normalized, and looks in both `{vault}/vault/raw/transcripts/`
  and `{vault}/raw/transcripts/` layouts. `.md` only. Folders starting with
  `.` or `_` are not vaults.

### 2. Display the table

The script prints a markdown table — show it as-is:

- **Origin category** — only the sub-path after `raw/transcripts` (`(root)` if none).
- **File** — transcript filename.
- **Target vault** — vault whose transcripts already contain it (blank `—` if none).
- **Status** — `copied` / `NOT COPIED`.

Plus a totals line and an "in target vaults but not in origin" section — flag
those to the user: they are transcripts that were copied/moved out of band, or
never passed through the inbox at all. Do not propose actions for them unless asked.

### 3. Propose the copies

For every `NOT COPIED` row, propose a destination — do not copy anything, only
propose. Re-run with `--copy-cmds` for a skeleton of cp commands you can fill in.

- **Destination vault:** infer from the filename's subject — match against the
  target vaults' existing categories first (e.g. `Kafka-*` → infra's
  `Kafka/`), then against their existing filenames. When several vaults fit,
  or nothing fits, list the candidates and ask.
- **Destination sub-folder:** reuse the target vault's existing category names
  before inventing a new one; propose `(root)` when the target vault has no
  sub-folders yet.
- Present one proposal block per pending file (group by vault when long):

```markdown
| File | Proposed destination |
| --- | --- |
| {file} | {vault}/raw/transcripts/{category}/ |

Copy commands:
```bash
cp "{origin}/vault/raw/transcripts/{category}/{file}" "{vault}/vault/raw/transcripts/{category}/{file}"
```
```

- Execute only on explicit user approval; create the destination folder if needed.

## Rules

- **Read-only by default.** The scan never writes; copies happen only after the
  user approves the proposal.
- **Never edit or normalise transcript content.** If a file looks garbled,
  point to `/lint-transcript-normalise` after it lands.
- **Don't ingest.** Once copied, filing into the wiki is `/second-brain-ingest`'s job.
- Copies are one-way inbox→vault; the vault copy is the keeper. The "in target
  but not in origin" section is informational.

## Chaining

Copy approved → optionally run `/lint-transcript-normalise` on the landed file
before `/second-brain-ingest`. Use `/change-management-1-stage` if the vaults
are git repos and the user wants the copies staged.
