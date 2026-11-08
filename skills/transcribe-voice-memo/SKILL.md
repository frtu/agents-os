---
name: transcribe-voice-memo
description: >
  Transcribe Apple Voice Memos using Whisper. Use when the user asks to
  "transcribe a voice memo", "transcribe recording", "convert voice memo
  to text", or mentions Voice Memos transcription. Supports direct
  invocation with memo name and language to skip prompts.
compatibility: Requires python3, ffprobe, whisper (pip install openai-whisper)
allowed-tools: Bash(PYTHONPATH=scripts python3 -m voice_memo*), Bash(PYTHONPATH=scripts python3 -m mode_selection*), Bash(bash scripts/transcribe.sh*)
metadata:
  version: "1.2.0"
variables:
  recording_path: "~/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings/*.m4a"
  target_path: "raw/transcripts/{YYYY-MM-DD} {recording-name}.md"
  max_recordings: 7
---

# Transcribe Voice Memo

Transcribe Apple Voice Memos to markdown using OpenAI Whisper.

## Argument Parsing

Parse the user's request for these optional inputs:

| Input         | How to detect                          | Example phrases                                               |
| ------------- | -------------------------------------- | ------------------------------------------------------------- |
| **Memo name** | Quoted text, backticks, or "named X"   | `Meeting-Notes`, "named Daily Standup", the one called Review |
| **Language**  | "in English", "from French", "English" | "transcribe in French", "from English"                        |
| **Latest**    | "latest", "most recent", "last"        | "transcribe latest voice memo"                                |

When inputs are provided, skip the corresponding prompts.

## Workflow

1. **Find recording** — If name/latest provided, filter directly; otherwise list and prompt
2. **Determine language** — If language provided, use it; otherwise prompt (default: English)
3. **Transcribe** — Run whisper with selected language
4. **Format output** — Apply template and save to `{target_path}`

## Step 1: Find Recording

**If user provided a memo name or "latest":**

```bash
PYTHONPATH=scripts python3 -m voice_memo list --name "<name_or_latest>"
```

This returns matching recordings. If exactly one match, proceed directly to transcription.
If multiple matches, present them for selection. If no matches, show all recent and ask.

**If no name provided:**

```bash
PYTHONPATH=scripts python3 -m voice_memo list --limit {max_recordings}
```

Present the list using AskUserQuestion with recording titles as options.

Output format: `title;path` (CSV), one per line, newest first.

## Step 2: Determine Language

**If user specified language** (e.g., "in English", "from French"): use it directly.

**Otherwise**, use **English** as the default (skip the prompt).

## Step 3: Transcribe

Run the transcription script:

```bash
bash scripts/transcribe.sh "<recording_path>" "<language>" "<output_path>" [device]
```

Arguments:
- `recording_path`: Full path to the .m4a file (from step 1 selection)
- `language`: "English", "French" or allow user to type
- `output_path`: **Absolute** path for the output markdown file (must be in user's vault, not skill folder)
- `device`: (optional) "auto" (default), "mps", or "cpu"

The output path should be constructed as an **absolute path** in the user's current working directory (the vault where the skill was invoked), NOT in the skill folder:
1. Start with the current working directory (e.g., `/Users/xxx`)
2. Append `{target_path}` template: `raw/transcripts/{YYYY-MM-DD} {recording-name}.md`
3. Replace `{YYYY-MM-DD}` with today's date
4. Replace `{recording-name}` with the recording title (sanitized for filename)

Example: If invoked from `/Users/xxx`, output to:
`/Users/xxx/raw/transcripts/2026-08-04 Meeting Notes.md`

### MPS Risk Evaluation (apply layer: script only)

With `device=auto`, the script scores the risk that Whisper fails on the GPU (MPS) and picks
the device. The scoring reads `config/risk_thresholds.json` **as-is**. No agent or LLM is
involved, and running a transcription never changes the thresholds.

| Factor | Why it adds risk |
| ------ | ---------------- |
| Long duration (above the *warn* / *safe* bounds) | NaN/inf errors accumulate over long audio in Whisper's attention layers |
| Recent MPS failure (within the failure window) | GPU state may still be unstable |
| Low free GPU memory | Memory pressure |
| High bitrate | Complex audio |

The score maps to a level (low → MPS, moderate → MPS with CPU fallback, high or critical →
CPU). The points, bounds and cut-offs live **only** in the JSON. Print them with:

```bash
PYTHONPATH=scripts python3 -m mode_selection show-config
```

### Auto-retry on MPS failure

If MPS fails with a tensor error, the script records the failure in `.mps_failures` and
retries on CPU, with no manual step. While the failure window is open, later runs see the
recent failure and go to CPU directly.

Every run also appends its outcome (duration, bitrate, codec, device, success, risk score) to
`config/transcription_stats.csv`. That is local data for calibration, not versioned. Logging
never changes the thresholds.

## Without an agent (apply-only)

Both scripts run from a plain shell, a cron job or a teammate's machine. They use the
thresholds as they are; the dictionary is **used, never grown**.

```bash
S=<skills-dir>/transcribe-voice-memo/scripts
bash $S/transcribe.sh "<recording.m4a>" English "<vault>/raw/transcripts/<YYYY-MM-DD> <name>.md"
bash $S/batch_transcribe.sh "<vault>/raw/transcripts/" English 10   # newest memos without a transcript
VOICE_MEMO_RISK_CONFIG=/path/to/pinned-thresholds.json bash $S/batch_transcribe.sh "<vault>/raw/transcripts/"
```

`batch_transcribe.sh` walks the newest recordings and stops at the first one that already has
a transcript. `VOICE_MEMO_RISK_CONFIG` points both scripts at another thresholds file, e.g. a
pinned copy shared across machines.

## Maintain the thresholds (optional: agent layer)

Calibration is the optional layer that makes the thresholds **evolve** from the logged
outcomes. It is a nice-to-have. Run it when the user asks, or offer it once after a
transcription reported an MPS failure. Never as a side effect of transcribing.

1. **Analyze.** `PYTHONPATH=scripts python3 -m mode_selection analyze`: MPS success and failure
   counts, longest success, shortest failure, suggested bounds.
2. **Preview.** `PYTHONPATH=scripts python3 -m mode_selection calibrate --dry-run` prints
   `old -> new` for the duration bounds.
3. **Ask, then apply.** Show the user the `old -> new` lines and the sample size behind them.
   Apply with `PYTHONPATH=scripts python3 -m mode_selection calibrate` only on their OK. Then
   report one line per changed value.

If the analysis prints `no_suggestion` (and `calibrate` refuses), duration does not separate
MPS successes from failures on this machine, e.g. MPS also fails on very short memos. Don't
force a value. Tell the user, and suggest `device=cpu` (or a pinned config) instead.

## Variables

- `{recording_path}`: Glob pattern for voice memo source files
  - Default: `~/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings/*.m4a`
- `{target_path}`: Output path template
  - Default: `raw/transcripts/{YYYY-MM-DD} {recording-name}.md`

## Output Format

The transcript is saved using the template in `references/transcribe_template.md`.

## Prerequisites

Ensure dependencies are installed:
- `ffprobe` (part of ffmpeg): `brew install ffmpeg`
- `whisper`: `pip install openai-whisper`
- Python 3.8+
