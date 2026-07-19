#!/bin/bash
set -euo pipefail

# Transcribe a voice memo using Whisper and format output with template
#
# Usage: transcribe.sh <audio_path> <language> <output_path> [device]
#
# Arguments:
#   audio_path  - Path to the .m4a file
#   language    - Language for transcription (English, French, etc.)
#   output_path - Path for the output markdown file
#   device      - (optional) "auto" (default), "mps", or "cpu"
#                 auto: evaluates MPS failure risk and chooses optimal device

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATE_FILE="$SKILL_DIR/references/transcribe_template.md"
MPS_FAILURE_LOG="$SKILL_DIR/.mps_failures"
HELPER_SCRIPT="$SCRIPT_DIR/list_recordings.py"

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 <audio_path> <language> <output_path>" >&2
    exit 1
fi

AUDIO_PATH="$1"
LANGUAGE="$2"
OUTPUT_PATH="$3"
DEVICE="${4:-auto}"

# Validate audio file exists
if [[ ! -f "$AUDIO_PATH" ]]; then
    echo "Error: Audio file not found: $AUDIO_PATH" >&2
    exit 1
fi

# Auto-select device using Python helper
if [[ "$DEVICE" == "auto" ]]; then
    echo "MPS Risk Evaluation:"

    # Get risk evaluation from Python helper
    RISK_OUTPUT=$(python3 "$HELPER_SCRIPT" risk "$AUDIO_PATH" --failure-log "$MPS_FAILURE_LOG")

    RISK_LEVEL=$(echo "$RISK_OUTPUT" | grep "^level:" | cut -d: -f2)
    RISK_SCORE=$(echo "$RISK_OUTPUT" | grep "^score:" | cut -d: -f2)
    USE_CPU=$(echo "$RISK_OUTPUT" | grep "^use_cpu:" | cut -d: -f2)
    RISK_REASONS=$(echo "$RISK_OUTPUT" | grep "^reasons:" | cut -d: -f2)
    DURATION=$(echo "$RISK_OUTPUT" | grep "^duration:" | cut -d: -f2)
    BITRATE=$(echo "$RISK_OUTPUT" | grep "^bitrate:" | cut -d: -f2)

    echo "  Duration: ${DURATION}s"
    echo "  Bitrate: ${BITRATE}kbps"
    echo "  Risk: $RISK_LEVEL (score: $RISK_SCORE)"
    [[ "$RISK_REASONS" != "none" ]] && echo "  Factors: $RISK_REASONS"
    echo ""

    if [[ "$USE_CPU" == "1" ]]; then
        DEVICE="cpu"
        echo "Using CPU (MPS risk too high)"
    else
        DEVICE="mps"
        echo "Using MPS (acceptable risk)"
    fi
    echo ""
fi

# Create temp directory for whisper output
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Get recording name from Python helper
META_OUTPUT=$(python3 "$HELPER_SCRIPT" metadata "$AUDIO_PATH")
RECORDING_NAME=$(echo "$META_OUTPUT" | grep "^title:" | cut -d: -f2-)

if [[ -z "$RECORDING_NAME" ]]; then
    RECORDING_NAME=$(basename "${AUDIO_PATH%.*}")
fi

# Get today's date
TODAY=$(date +%Y-%m-%d)

echo "Transcribing: $RECORDING_NAME"
echo "Language: $LANGUAGE"
echo "Device: $DEVICE"
echo ""

# Run whisper transcription
START_TIME=$(date +%s)
ERROR_LOG="$TEMP_DIR/whisper_error.log"

run_whisper() {
    local device="$1"
    whisper "$AUDIO_PATH" \
        --language "$LANGUAGE" \
        --output_format txt \
        --output_dir "$TEMP_DIR" \
        --model turbo \
        --device "$device" \
        --verbose False
}

AUDIO_BASENAME=$(basename "${AUDIO_PATH%.*}")
TXT_FILE="$TEMP_DIR/$AUDIO_BASENAME.txt"

set +e
if [[ "$DEVICE" == "mps" ]]; then
    run_whisper mps >"$ERROR_LOG" 2>&1
    WHISPER_EXIT=$?

    # Check for MPS tensor errors
    if [[ $WHISPER_EXIT -ne 0 ]] || ! [[ -f "$TXT_FILE" ]]; then
        if grep -qiE "(nan|inf|ValueError|invalid values|Skipping)" "$ERROR_LOG"; then
            echo ""
            echo "MPS failed with tensor error, recording failure and retrying with CPU..."
            python3 "$HELPER_SCRIPT" record-failure --failure-log "$MPS_FAILURE_LOG"
            echo ""
            DEVICE="cpu"
            rm -f "$TEMP_DIR"/*.txt
            run_whisper cpu
            WHISPER_EXIT=$?
        else
            cat "$ERROR_LOG" >&2
            exit 1
        fi
    else
        cat "$ERROR_LOG"
    fi
else
    run_whisper "$DEVICE"
    WHISPER_EXIT=$?
fi
set -e

if [[ $WHISPER_EXIT -ne 0 ]]; then
    echo "Error: Whisper transcription failed" >&2
    exit 1
fi

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

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
TEMPLATE=$(cat "$TEMPLATE_FILE")
OUTPUT="$TEMPLATE"
OUTPUT="${OUTPUT//\{recording-name\}/$RECORDING_NAME}"
OUTPUT="${OUTPUT//\{YYYY-MM-DD\}/$TODAY}"
OUTPUT="${OUTPUT//\{language\}/$LANGUAGE}"
OUTPUT="${OUTPUT//\{transcript\}/$TRANSCRIPT}"
echo "$OUTPUT" > "$OUTPUT_PATH"

# Record success
record_result "$ACTUAL_DEVICE" "true"

echo ""
echo "Transcription complete"
echo "  Time: ${ELAPSED}s"
echo "  File: $OUTPUT_PATH"
