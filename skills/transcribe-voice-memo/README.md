# Transcribe Voice Memo

Transcribe Apple Voice Memos to markdown using OpenAI Whisper with intelligent MPS/CPU device selection.

## Features

- **Voice Memo Discovery**: List and search Apple Voice Memos by name
- **Metadata Extraction**: Get title, duration, and bitrate using ffprobe
- **Smart Device Selection**: Automatically choose MPS (GPU) or CPU based on failure risk
- **MPS Risk Evaluation**: Score-based system considering duration, recent failures, GPU memory, and bitrate
- **Auto-Fallback**: Retry with CPU if MPS fails with tensor errors
- **Statistics & Calibration**: Track outcomes and auto-tune thresholds from real data

## Project Structure

```
transcribe-voice-memo/
├── SKILL.md                 # Skill definition for Claude Code
├── README.md                # This file
├── config/
│   ├── risk_thresholds.json # MPS risk evaluation config
│   └── transcription_stats.csv  # Outcome statistics (generated)
├── references/
│   └── transcribe_template.md   # Output template
├── scripts/
│   ├── transcribe.sh        # Main transcription script
│   ├── voice_memo/          # Voice memo helper module
│   │   ├── __init__.py      # VoiceMemoHelper, AudioMetadata
│   │   └── __main__.py      # CLI entry point
│   ├── mode_selection/      # MPS risk evaluation module
│   │   ├── __init__.py      # RiskEvaluator, RiskConfig, TranscriptionStats
│   │   └── __main__.py      # CLI entry point
│   └── tests/               # Unit tests
│       ├── __init__.py
│       ├── test_voice_memo.py
│       └── test_mode_selection.py
└── .mps_failures            # Recent MPS failure log (generated)
```

## Requirements

- Python 3.8+
- ffmpeg/ffprobe: `brew install ffmpeg`
- openai-whisper: `pip install openai-whisper`

## Usage

### Transcribe a Voice Memo

```bash
cd scripts
bash transcribe.sh "<audio_path>" "<language>" "<output_path>" [device]
```

Arguments:
- `audio_path`: Path to .m4a file
- `language`: "English", "French", etc.
- `output_path`: Where to save the markdown transcript
- `device`: "auto" (default), "mps", or "cpu"

### Voice Memo Module

```bash
cd scripts

# List recent recordings
python -m voice_memo list --limit 5

# Search by name
python -m voice_memo list --name "meeting"

# Get metadata
python -m voice_memo metadata "/path/to/recording.m4a"
python -m voice_memo metadata "/path/to/recording.m4a" --json
```

### Mode Selection Module

```bash
cd scripts

# Evaluate MPS risk
python -m mode_selection evaluate --duration 1800 --bitrate 128

# Show current config
python -m mode_selection show-config

# Record a transcription result
python -m mode_selection record-result --device mps --duration 1200 --success

# Analyze statistics
python -m mode_selection analyze

# Calibrate thresholds from statistics
python -m mode_selection calibrate --dry-run  # Preview
python -m mode_selection calibrate            # Apply
```

## Running Tests

```bash
# From scripts/ directory
cd scripts
python -m unittest discover -s tests -v

# From project root
python -m unittest discover -s scripts/tests -t scripts -v

# Run specific test module (from scripts/)
cd scripts
python -m unittest tests.test_voice_memo -v
python -m unittest tests.test_mode_selection -v
```

## MPS Risk Evaluation

MPS (Metal Performance Shaders) on Apple Silicon can fail during Whisper transcription due to numerical instability. The risk evaluator scores multiple factors:

| Factor | Points | Condition |
|--------|--------|-----------|
| Long duration | +40 | > 30 min (warn threshold) |
| Medium duration | +20 | > 25 min (safe threshold) |
| Recent MPS failure | +30 | Within 1 hour |
| Low GPU memory | +25 | < 2GB free |
| High bitrate | +10 | > 256 kbps |

**Risk Levels:**
- **Low** (0-14): Use MPS
- **Moderate** (15-29): Use MPS with fallback
- **High** (30-49): Use CPU directly
- **Critical** (50+): Use CPU directly

## Configuration

Edit `config/risk_thresholds.json` to adjust thresholds:

```json
{
  "duration": {
    "safe": 1500,
    "warn": 1800
  },
  "bitrate_high": 256,
  "gpu_min_free_mb": 2048,
  "scores": {
    "duration_high": 40,
    "duration_moderate": 20,
    "recent_failure": 30,
    "low_memory": 25,
    "high_bitrate": 10
  },
  "thresholds": {
    "critical": 50,
    "high": 30,
    "moderate": 15
  }
}
```

Or use `calibrate` to auto-tune from your transcription history.

## License

Internal tool for personal knowledge base management.
