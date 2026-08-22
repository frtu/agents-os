---
name: claude-permissions-compress
description: >
  Interactively compress a Claude Code permissions file (settings.local.json).
  Reviews the allow-list for redundancy, groups entries by topic, translates each
  into plain language with a danger rating, and applies a consolidated wildcard
  one topic at a time — asking the user to approve or correct each step. Use when
  the user says "compress settings", "compress permissions", "clean up
  settings.local.json", or "the allow-list is too long".
allowed-tools: Read Edit Bash AskUserQuestion
---

# Compress Permissions (interactive)

Shrink a bloated `permissions.allow` list into a small set of reviewed wildcards,
**one topic at a time**, keeping the user in control of every scope change.

The allow-list controls which tool calls run without a confirmation prompt.
Widening it trades safety for convenience — so every consolidation is a security
decision the user must sign off on. Never widen scope silently.

## Input

| Parameter | Description | Default |
| --------- | ----------- | ------- |
| `file` | Path to the permissions file to compress | `.claude/settings.local.json` |

## Golden rules (never break)

1. **One topic per approval.** Present a single topic, apply it only after the user
   approves, then move on. Never batch-apply.
2. **Never auto-widen destructive verbs.** `kill`, `pkill`, `rm` (outside a tightly
   scoped temp dir), `git reset --hard`, `git push`, `git commit`, `--force`,
   `--no-verify`, `chmod`, `sudo`, credential/secret reads, and anything that writes
   outside the project must stay **explicit** (or be dropped so they re-prompt).
   Flag them as high danger and recommend *against* wildcarding.
3. **Validate after every apply.** Run the JSON check below; if it fails, revert that
   edit and tell the user.
4. **Back up once, before the first edit.**
5. **Translate both ways.** Show plain English for what exists; when the user proposes
   a correction in words, translate it back into exact permission syntax and echo it
   for confirmation before applying.

## Workflow

### 1. Load and back up

```bash
cp {file} {file}.bak
```

Read `{file}` and parse `permissions.allow`. If the file is missing or has no
`allow` array, report and stop.

### 2. Group by topic

Bucket every entry into topics by the leading command / intent. Typical topics:

| Topic | Example members |
| ----- | --------------- |
| echo / logging | `Bash(echo "started pid $!")` … |
| curl smoke tests | `Bash(curl -s localhost:8123/health)` … (many ports) |
| server launches | `Bash(LEADER_PORT=8123 uv run *)` … (many ports) |
| package/build | `uv run *`, `uv sync *`, `npx tsc *`, `uv pip *` |
| git (read-only) | `git -C * log *`, `git status` |
| git (mutating) | `git add *`, `git commit *`, `git reset *` |
| text tools | `grep *`, `sed *`, `sort *` |
| browser | `agent-browser *` |
| file reads | `Read(...)` |
| process control | `kill *`, `pkill *`, `lsof *`, `ps *` |
| destructive | `rm -rf *` |

For each topic compute a **redundancy score** = number of near-duplicate entries that
collapse into one wildcard (higher = more worth doing).

### 3. Order the topics

Sort the queue by: **most redundant first, least dangerous first** (redundancy as the
primary key, danger as the tiebreaker — so the highest-value, safest wins lead). Put
destructive/process-control topics last, and mark them "review only — recommend no
wildcard."

Present the ordered plan to the user as a checklist so they see the whole path:

```
Topics to review (in order):
1. curl smoke tests   — 41 entries → 1   (danger: LOW)
2. echo / logging     —  7 entries → 1   (danger: LOW)
3. server launches    — 12 entries → 3   (danger: LOW)
...
N. process control    —  5 entries       (danger: HIGH — recommend keep explicit)
```

### 4. Iterate — one topic at a time

For the current topic, show a compact card:

```
── Topic: curl smoke tests ────────────────────────────
Redundant entries (41):
  Bash(curl -s localhost:8123/health)
  Bash(curl -s localhost:8124/health)
  ... (+39 more, varying only by port/path)

Plain English: run read-only HTTP requests against a local dev server.
Proposed:      Bash(curl -s *)
Danger:        LOW — read-only, but a wildcard also permits curl to ANY
               host (e.g. exfil to a remote URL). Narrow to localhost if
               you want to keep it local: Bash(curl -s localhost:*)
```

**Danger scale:**
- **LOW** — read-only, local, easily reversible (echo, curl GET, reads, `ls`, `git log`).
- **MEDIUM** — mutates local state or launches processes (`uv run`, `git add`, `mkdir`,
  server launches, `sed -i`).
- **HIGH** — hard to reverse, affects shared state, or destructive (`kill`/`pkill`,
  `rm`, `git push`/`reset --hard`/`commit`, `--force`, `sudo`, secret reads, network
  writes). Recommend keeping explicit.

Then ask with `AskUserQuestion` (one question, options):
- **Approve** — apply the proposed wildcard.
- **Approve (narrower)** — apply the safer narrowed variant you offered.
- **Edit** — user describes what they want in words; you translate to syntax, echo it,
  then apply.
- **Skip** — leave this topic untouched.

If **Edit**: convert the natural-language request into an exact permission string,
show it back ("You said 'only allow curl to localhost and 127.0.0.1' → I'll add
`Bash(curl -s localhost:*)` and `Bash(curl -s 127.0.0.1:*)` and drop the 41 per-port
lines. Apply?"), and only apply on confirmation.

### 5. Apply one topic

Edit `{file}`: remove the collapsed members, insert the approved wildcard(s). Then:

```bash
python3 -c "import json;json.load(open('{file}'));print('valid JSON')"
```

If invalid, restore from `{file}.bak`'s relevant section (or re-edit) and report.
Report the running tally: `Topic N applied — allow-list now M entries (was K).`

### 6. Next topic

Repeat step 4–5 until the queue is empty. Re-prompt automatically for the next topic;
don't wait to be told "continue" unless the user asked to go slowly.

### 7. Final report

```
Compression complete.
  Before: K entries
  After:  M entries  (−X%)
Kept explicit (by design, still prompt): kill, pkill, rm, git push …
Backup: {file}.bak
```

Remind the user the `.bak` can be deleted once they're happy, and that any command
still not in the list will simply prompt as before — nothing was made *less* safe than
an explicit deny.

## Edge cases

- **Already generic:** if a topic is a single wildcard already, note it and skip.
- **Mixed-danger topic:** split it — wildcard the safe members, list the risky ones
  separately and recommend keeping them explicit.
- **User approves a HIGH-danger wildcard anyway:** confirm once more, quoting the
  specific risk, before applying.
- **No redundancy found:** report the file is already compact and stop.
