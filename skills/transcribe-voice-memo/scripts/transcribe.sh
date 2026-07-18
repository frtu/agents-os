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

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 <audio_path> <language> <output_path>" >&2
    exit 1
fi

AUDIO_PATH="$1"
LANGUAGE="$2"
OUTPUT_PATH="$3"
DEVICE="${4:-auto}"

# ============================================================================
# MPS FAILURE RISK EVALUATION
# ============================================================================
# MPS (Metal Performance Shaders) on Apple Silicon can fail due to:
#   1. Numerical instability in attention layers (NaN/inf in logits tensor)
#   2. GPU memory pressure from other processes
#   3. Long audio accumulating floating-point errors
#   4. Complex audio patterns stressing the decoder
#
# Risk factors (empirically observed):
#   - Duration >5min: moderate risk (errors accumulate)
#   - Duration >8min: high risk
#   - Recent MPS failures: GPU state may be unstable
#   - High GPU memory usage: reduces available workspace
#   - High bitrate/complex audio: more computation per segment
# ============================================================================

# Empirically calibrated from real transcriptions:
#   - 27min (1642s) succeeded with MPS
#   - 32min (1919s) failed at 2%
#   - 47min (2846s) failed at 44%
MPS_SAFE_DURATION=1500     # 25 min - low risk threshold
MPS_WARN_DURATION=1800     # 30 min - high risk threshold
MPS_FAILURE_WINDOW=3600    # 1 hour - consider recent failures
MPS_MIN_GPU_FREE_MB=2048   # Minimum free GPU memory for MPS

# Validate audio file exists
if [[ ! -f "$AUDIO_PATH" ]]; then
    echo "Error: Audio file not found: $AUDIO_PATH" >&2
    exit 1
fi

# Get audio duration in seconds
get_duration() {
    ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$1" 2>/dev/null | cut -d. -f1
}

# Get audio bitrate in kbps
get_bitrate() {
    ffprobe -v quiet -show_entries format=bit_rate -of csv=p=0 "$1" 2>/dev/null | awk '{print int($1/1000)}'
}

# Check if MPS failed recently (within failure window)
has_recent_mps_failure() {
    if [[ ! -f "$MPS_FAILURE_LOG" ]]; then
        return 1
    fi
    local now=$(date +%s)
    local cutoff=$((now - MPS_FAILURE_WINDOW))
    # Check if any failure timestamp is within window
    while read -r timestamp; do
        if [[ -n "$timestamp" ]] && [[ "$timestamp" -gt "$cutoff" ]]; then
            return 0
        fi
    done < "$MPS_FAILURE_LOG"
    return 1
}

# Record an MPS failure
record_mps_failure() {
    echo "$(date +%s)" >> "$MPS_FAILURE_LOG"
    # Keep only last 10 entries
    if [[ -f "$MPS_FAILURE_LOG" ]]; then
        tail -10 "$MPS_FAILURE_LOG" > "$MPS_FAILURE_LOG.tmp"
        mv "$MPS_FAILURE_LOG.tmp" "$MPS_FAILURE_LOG"
    fi
}

# Get approximate free GPU memory (macOS specific)
get_gpu_free_mb() {
    # Use vm_stat and system memory as proxy (MPS shares unified memory)
    local free_pages=$(vm_stat 2>/dev/null | awk '/Pages free/ {gsub(/\./,"",$3); print $3}')
    local inactive_pages=$(vm_stat 2>/dev/null | awk '/Pages inactive/ {gsub(/\./,"",$3); print $3}')
    if [[ -n "$free_pages" ]] && [[ -n "$inactive_pages" ]]; then
        # Page size is 16384 bytes on Apple Silicon
        echo $(( (free_pages + inactive_pages) * 16384 / 1024 / 1024 ))
    else
        echo "0"
    fi
}

# Evaluate MPS failure risk (returns: low, moderate, high, critical)
evaluate_mps_risk() {
    local duration="$1"
    local bitrate="$2"
    local risk_score=0
    local risk_reasons=()

    # Factor 1: Duration
    if [[ -n "$duration" ]]; then
        if [[ "$duration" -gt "$MPS_WARN_DURATION" ]]; then
            risk_score=$((risk_score + 40))
            risk_reasons+=("duration>${MPS_WARN_DURATION}s")
        elif [[ "$duration" -gt "$MPS_SAFE_DURATION" ]]; then
            risk_score=$((risk_score + 20))
            risk_reasons+=("duration>${MPS_SAFE_DURATION}s")
        fi
    fi

    # Factor 2: Recent failures
    if has_recent_mps_failure; then
        risk_score=$((risk_score + 30))
        risk_reasons+=("recent_failure")
    fi

    # Factor 3: GPU memory
    local gpu_free=$(get_gpu_free_mb)
    if [[ -n "$gpu_free" ]] && [[ "$gpu_free" -lt "$MPS_MIN_GPU_FREE_MB" ]]; then
        risk_score=$((risk_score + 25))
        risk_reasons+=("low_memory:${gpu_free}MB")
    fi

    # Factor 4: High bitrate (>256kbps suggests complex audio)
    if [[ -n "$bitrate" ]] && [[ "$bitrate" -gt 256 ]]; then
        risk_score=$((risk_score + 10))
        risk_reasons+=("high_bitrate:${bitrate}kbps")
    fi

    # Determine risk level
    local risk_level
    if [[ $risk_score -ge 50 ]]; then
        risk_level="critical"
    elif [[ $risk_score -ge 30 ]]; then
        risk_level="high"
    elif [[ $risk_score -ge 15 ]]; then
        risk_level="moderate"
    else
        risk_level="low"
    fi

    echo "$risk_level|${risk_reasons[*]:-none}|$risk_score"
}

# Auto-select device based on risk evaluation
if [[ "$DEVICE" == "auto" ]]; then
    DURATION=$(get_duration "$AUDIO_PATH")
    BITRATE=$(get_bitrate "$AUDIO_PATH")

    RISK_RESULT=$(evaluate_mps_risk "$DURATION" "$BITRATE")
    RISK_LEVEL=$(echo "$RISK_RESULT" | cut -d'|' -f1)
    RISK_REASONS=$(echo "$RISK_RESULT" | cut -d'|' -f2)
    RISK_SCORE=$(echo "$RISK_RESULT" | cut -d'|' -f3)

    echo "MPS Risk Evaluation:"
    echo "  Duration: ${DURATION:-unknown}s"
    echo "  Bitrate: ${BITRATE:-unknown}kbps"
    echo "  Risk: $RISK_LEVEL (score: $RISK_SCORE)"
    [[ "$RISK_REASONS" != "none" ]] && echo "  Factors: $RISK_REASONS"
    echo ""

    if [[ "$RISK_LEVEL" == "critical" ]] || [[ "$RISK_LEVEL" == "high" ]]; then
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
echo "Device: $DEVICE"
echo ""

# Run whisper transcription (MPS for Apple Silicon GPU, CPU as fallback)
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

# Disable exit-on-error for whisper call to handle MPS failures
AUDIO_BASENAME=$(basename "${AUDIO_PATH%.*}")
TXT_FILE="$TEMP_DIR/$AUDIO_BASENAME.txt"

set +e
if [[ "$DEVICE" == "mps" ]]; then
    run_whisper mps >"$ERROR_LOG" 2>&1
    WHISPER_EXIT=$?

    # Check for MPS tensor errors (whisper may exit 0 but skip the file)
    if [[ $WHISPER_EXIT -ne 0 ]] || ! [[ -f "$TXT_FILE" ]]; then
        if grep -qiE "(nan|inf|ValueError|invalid values|Skipping)" "$ERROR_LOG"; then
            echo ""
            echo "MPS failed with tensor error, recording failure and retrying with CPU..."
            record_mps_failure
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
