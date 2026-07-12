---
name: transcribe-voice-memo
description: >
  Transcribe Apple Voice Memos using Whisper. Lists recent recordings,
  prompts for selection and language, then outputs a formatted markdown
  transcript. Use when the user asks to "transcribe a voice memo",
  "transcribe recording", "convert voice memo to text", or mentions
  Voice Memos transcription.
compatibility: Requires python3, ffprobe, whisper (pip install openai-whisper)
allowed-tools: Bash(python3 *list_recordings.py*), Bash(bash *transcribe.sh*)
metadata:
  version: "1.0.0"
variables:
  recording_path: "~/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings/*.m4a"
  target_path: "raw/transcripts/{YYYY-MM-DD} {recording-name}.md"
---

# Transcribe Voice Memo

Transcribe Apple Voice Memos to markdown using OpenAI Whisper.

## Workflow

1. **List recordings** — Show the 5 most recent voice memos
2. **User selects recording** — Present the list and ask which to transcribe
3. **Select language** — Ask: English (default) or French
4. **Transcribe** — Run whisper with selected language
5. **Format output** — Apply template and save to `{target_path}`

## Step 1: List Recordings

Run the listing script to get recent voice memos:

```bash
python3 scripts/list_recordings.py --limit 5
```

Output format: `title;path` (CSV), one per line, newest first.

Present these to the user using AskUserQuestion with the recording titles as options.

## Step 2: Select Language

After the user selects a recording, ask for the language:
- **English** (default)
- **French**

## Step 3: Transcribe

Run the transcription script:

```bash
bash scripts/transcribe.sh "<recording_path>" "<language>" "<output_path>"
```

Arguments:
- `recording_path`: Full path to the .m4a file (from step 1 selection)
- `language`: "English" or "French"
- `output_path`: Target file path, e.g., `raw/transcripts/2026-07-12 Meeting Notes.md`

The output path should be constructed from `{target_path}` variable:
- Replace `{YYYY-MM-DD}` with today's date
- Replace `{recording-name}` with the recording title (sanitized for filename)

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
