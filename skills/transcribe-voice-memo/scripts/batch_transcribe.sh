#!/bin/bash
set -euo pipefail

# Batch transcribe the most recent voice memos that don't yet have a transcript.
#
# Usage: batch_transcribe.sh <target_folder> [language] [limit]
#
# Arguments:
#   target_folder - The final folder where transcripts are written, i.e.
#                   {workspace}/vault/raw/transcripts/ (no subfolder is appended)
#   language      - (optional) Whisper language (default: English)
#   limit         - (optional) Maximum number of most-recent recordings to
#                   consider (default: 10)
#
# Behavior:
#   1. List the <limit> most recent recordings (newest first, by mtime).
#   2. Walk them from most recent to oldest.
#   3. As soon as a recording already has a transcript in the target, stop:
#      everything older is assumed to be done.
#   4. Otherwise transcribe it source -> target via transcribe.sh, as
#      "{YYYY-MM-DD} {recording-name}.md" (date = transcription day).

DEFAULT_LIMIT=10

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRANSCRIBE="$SCRIPT_DIR/transcribe.sh"

export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <target_folder> [language] [limit]" >&2
    exit 1
fi

TARGET_FOLDER="$1"
LANGUAGE="${2:-English}"
LIMIT="${3:-$DEFAULT_LIMIT}"

if [[ ! "$LIMIT" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: limit must be a positive integer, got: $LIMIT" >&2
    exit 1
fi

if [[ ! -d "$TARGET_FOLDER" ]]; then
    echo "Error: Target folder not found: $TARGET_FOLDER" >&2
    exit 1
fi

TRANSCRIPTS_DIR="$TARGET_FOLDER"
TODAY=$(date +%Y-%m-%d)

sanitize() {
    # Make a title safe as a filename
    echo "$1" | tr '/\\:|?*"' '-' | sed -E 's/[[:space:]]+/ /g; s/^ //; s/ $//'
}

# Check if a recording title already has a transcript in the target.
# Transcripts are named "{YYYY-MM-DD} {title}.md" (date = transcription day,
# which varies), so match on the " {title}.md" / "{title}.md" suffix.
has_transcript() {
    local sanitized
    sanitized=$(sanitize "$1")
    local f base
    for f in "$TRANSCRIPTS_DIR"/*.md; do
        [[ -e "$f" ]] || continue
        base=$(basename "$f")
        if [[ "$base" == "$sanitized.md" || "$base" == *" $sanitized.md" ]]; then
            return 0
        fi
    done
    return 1
}

# Get the <limit> most recent recordings, newest first: "title;path" per line
if ! RECORDINGS=$(python3 -m voice_memo list --limit "$LIMIT") || [[ -z "$RECORDINGS" ]]; then
    echo "No recordings found."
    exit 0
fi

lines=()
while IFS= read -r line; do
    [[ -n "$line" ]] && lines+=("$line")
done <<< "$RECORDINGS"

echo "Checking the ${#lines[@]} most recent recording(s), newest first -> $TRANSCRIPTS_DIR"
echo ""

FAILURES=0
COMPLETED=0
SEEN=""   # sanitized titles handled in this run (transcripts are keyed by title)
for line in "${lines[@]}"; do
    title="${line%;*}"
    path="${line##*;}"
    sanitized=$(sanitize "$title")

    if has_transcript "$title"; then
        echo "Already transcribed: $title"
        echo "Stopping: this and all older recordings are assumed up to date."
        break
    fi

    if [[ $'\n'"$SEEN" == *$'\n'"$sanitized"$'\n'* ]]; then
        echo "Skipping duplicate title in this run: $title"
        continue
    fi
    SEEN+="$sanitized"$'\n'

    output_path="$TRANSCRIPTS_DIR/$TODAY $sanitized.md"
    echo "================================================================"
    echo "$title"
    echo "================================================================"
    if bash "$TRANSCRIBE" "$path" "$LANGUAGE" "$output_path"; then
        COMPLETED=$(( COMPLETED + 1 ))
    else
        echo "Warning: transcription failed for: $title" >&2
        FAILURES=$(( FAILURES + 1 ))
    fi
    echo ""
done

echo "Batch complete: $COMPLETED succeeded, $FAILURES failed."
[[ "$FAILURES" -eq 0 ]] || exit 1
