---
name: transcribe-voice-memo
description: >
  Transcribe Apple Voice Memos using Whisper. Use when the user asks to
  "transcribe a voice memo", "transcribe recording", "convert voice memo
  to text", or mentions Voice Memos transcription. Supports direct
  invocation with memo name and language to skip prompts.
compatibility: Requires python3, ffprobe, whisper (pip install openai-whisper)
allowed-tools: Bash(python3 *list_recordings.py*), Bash(bash *transcribe.sh*)
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
python3 -m voice_memo list --name "<name_or_latest>"
```

This returns matching recordings. If exactly one match, proceed directly to transcription.
If multiple matches, present them for selection. If no matches, show all recent and ask.

**If no name provided:**

```bash
python3 -m voice_memo list --limit {max_recordings}
```

Present the list using AskUserQuestion with recording titles as options.

Output format: `title;path` (CSV), one per line, newest first.

## Step 2: Determine Language

**If user specified language** (e.g., "in English", "from French"): use it directly.

**Otherwise**, ask for the language:
- **English** (default)
- **French**

## Step 3: Transcribe

Run the transcription script:

```bash
bash scripts/transcribe.sh "<recording_path>" "<language>" "<output_path>" [device]
```

Arguments:
- `recording_path`: Full path to the .m4a file (from step 1 selection)
- `language`: "English" or "French"
- `output_path`: Target file path, e.g., `raw/transcripts/2026-07-12 Meeting Notes.md`
- `device`: (optional) "auto" (default), "mps", or "cpu"

The output path should be constructed from `{target_path}` variable:
- Replace `{YYYY-MM-DD}` with today's date
- Replace `{recording-name}` with the recording title (sanitized for filename)

### MPS Risk Evaluation

The script evaluates MPS failure risk using multiple factors:

| Factor                   | Risk Points | Threshold                 |
| ------------------------ | ----------- | ------------------------- |
| Duration >30min          | +40         | High risk                 |
| Duration >25min          | +20         | Moderate risk             |
| Recent MPS failure (1hr) | +30         | GPU state may be unstable |
| Low GPU memory (<2GB)    | +25         | Memory pressure           |
| High bitrate (>256kbps)  | +10         | Complex audio             |

**Risk levels:**
- **Low** (0-14): Use MPS
- **Moderate** (15-29): Use MPS with fallback
- **High** (30-49): Use CPU directly
- **Critical** (50+): Use CPU directly

**Why MPS fails:** NaN/inf tensor errors in Whisper's attention layers due to numerical instability accumulating over long audio segments.

### Auto-retry on MPS failure

If MPS fails unexpectedly (tensor errors), the script:
1. Records the failure (for future risk evaluation)
2. Automatically retries with CPU
3. No manual intervention needed

Failure history persists for 1 hour, so subsequent transcriptions will detect the recent failure and use CPU preemptively.

### Statistics & Calibration

The script records every transcription outcome to `config/transcription_stats.csv`:
- timestamp, duration, bitrate, device, success/failure, risk level/score
- file_size_bytes, sample_rate_hz, channels, codec (for failure analysis)

**Analyze statistics:**
```bash
python3 -m mode_selection analyze
```

Returns: total records, MPS success/failure counts, max successful duration, min failed duration, and suggested threshold updates.

**Calibrate thresholds from statistics:**
```bash
python3 -m mode_selection calibrate --dry-run  # preview changes
python3 -m mode_selection calibrate            # apply changes
```

Updates `config/risk_thresholds.json` with duration thresholds derived from actual success/failure patterns.

**Show current config:**
```bash
python3 -m mode_selection show-config
```

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
