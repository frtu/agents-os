# Getting Started: Batch Transcribe

Run `scripts/batch_transcribe.sh` manually to transcribe your latest voice memos that don't yet have a transcript in your vault.

## Prerequisites

- `ffmpeg` (includes `ffprobe`): `brew install ffmpeg`
- `whisper`: `pip install openai-whisper`
- Python 3.8+

## Usage

```bash
bash scripts/batch_transcribe.sh <target_folder> [language] [limit]
```

| Argument        | Required | Default | Description                                                                          |
| --------------- | -------- | ------- | ------------------------------------------------------------------------------------ |
| `target_folder` | Yes      | —       | Final transcripts folder: `{workspace}/vault/raw/transcripts/` (nothing is appended) |
| `language`      | No       | English | Whisper language (e.g. English, French)                                              |
| `limit`         | No       | 10      | Maximum number of most recent recordings to consider                                 |

## What it does

1. Lists the `limit` most recent recordings in the Apple Voice Memos folder (newest first)
2. Walks them from most recent to oldest
3. Stops at the first recording that already has a transcript (everything older is assumed done)
4. Otherwise transcribes it, saving to:
   `{workspace}/vault/raw/transcripts/{YYYY-MM-DD} {recording-name}.md`
   (`{YYYY-MM-DD}` is the transcription day)

## Examples

```bash
# Transcribe the latest 10 missing memos, in English
bash scripts/batch_transcribe.sh ~/my-workspace/vault/raw/transcripts

# Same, but in French
bash scripts/batch_transcribe.sh ~/my-workspace/vault/raw/transcripts French

# Consider the 30 most recent recordings instead of 10
bash scripts/batch_transcribe.sh ~/my-workspace/vault/raw/transcripts English 30
```

## Notes

- Device selection (MPS vs CPU) and auto-retry are handled by `transcribe.sh` per recording
- A failed recording is logged and skipped; the script continues with the rest and exits non-zero at the end if any failed
- Existing transcripts are matched by recording name (the date prefix is ignored), so a memo transcribed on another day is still detected
- Recordings with duplicate titles are transcribed once (transcripts are keyed by title)
- Long runs take time — Whisper runs sequentially; roughly ~1 min of processing per minute of audio on CPU, faster on MPS
