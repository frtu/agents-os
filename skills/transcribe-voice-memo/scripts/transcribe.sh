#!/bin/bash
set -euo pipefail

# Transcribe a voice memo using Whisper and format output with template
#
# Usage: transcribe.sh <audio_path> <language> <output_path>
#
# Arguments:
#   audio_path  - Path to the .m4a file
#   language    - Language for transcription (English, French, etc.)
#   output_path - Path for the output markdown file

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATE_FILE="$SKILL_DIR/references/transcribe_template.md"

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 <audio_path> <language> <output_path>" >&2
    exit 1
fi

AUDIO_PATH="$1"
LANGUAGE="$2"
OUTPUT_PATH="$3"

# Validate audio file exists
if [[ ! -f "$AUDIO_PATH" ]]; then
    echo "Error: Audio file not found: $AUDIO_PATH" >&2
    exit 1
fi

# Create temp directory for whisper output
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Get recording name from audio file metadata or filename
RECORDING_NAME=$(ffprobe -v quiet -print_format json -show_entries format_tags=title "$AUDIO_PATH" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('format',{}).get('tags',{}).get('title',''))" 2>/dev/null || true)

if [[ -z "$RECORDING_NAME" ]]; then
    # Fallback to filename without extension
    RECORDING_NAME=$(basename "${AUDIO_PATH%.*}")
fi

# Get today's date
TODAY=$(date +%Y-%m-%d)

echo "Transcribing: $RECORDING_NAME"
echo "Language: $LANGUAGE"
echo ""

# Run whisper transcription using MPS (Metal Performance Shaders) on Apple Silicon
START_TIME=$(date +%s)
whisper "$AUDIO_PATH" \
    --language "$LANGUAGE" \
    --output_format txt \
    --output_dir "$TEMP_DIR" \
    --model turbo \
    --device mps \
    --verbose False
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

# Find the output txt file
AUDIO_BASENAME=$(basename "${AUDIO_PATH%.*}")
TXT_FILE="$TEMP_DIR/$AUDIO_BASENAME.txt"

if [[ ! -f "$TXT_FILE" ]]; then
    echo "Error: Transcription output not found: $TXT_FILE" >&2
    exit 1
fi

# Read transcript
TRANSCRIPT=$(cat "$TXT_FILE")

# Ensure output directory exists
OUTPUT_DIR=$(dirname "$OUTPUT_PATH")
mkdir -p "$OUTPUT_DIR"

# Apply template
if [[ -f "$TEMPLATE_FILE" ]]; then
    # Read template and substitute variables
    TEMPLATE=$(cat "$TEMPLATE_FILE")

    # Perform substitutions
    OUTPUT="$TEMPLATE"
    OUTPUT="${OUTPUT//\{recording-name\}/$RECORDING_NAME}"
    OUTPUT="${OUTPUT//\{YYYY-MM-DD\}/$TODAY}"
    OUTPUT="${OUTPUT//\{language\}/$LANGUAGE}"
    OUTPUT="${OUTPUT//\{transcript\}/$TRANSCRIPT}"

    echo "$OUTPUT" > "$OUTPUT_PATH"
else
    # Fallback: create simple markdown output
    cat > "$OUTPUT_PATH" << EOF
---
title: "$RECORDING_NAME"
date: "$TODAY"
language: "$LANGUAGE"
source: Voice Memo
---

# $RECORDING_NAME

$TRANSCRIPT
EOF
fi

echo ""
echo "Transcription complete"
echo "  Time: ${ELAPSED}s"
echo "  File: $OUTPUT_PATH"
