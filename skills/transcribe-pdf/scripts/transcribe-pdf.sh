#!/bin/bash
# transcribe-pdf.sh — entry point. Bootstraps a private venv, then runs the orchestrator.
#
# Usage:
#   transcribe-pdf.sh <file-or-dir> [...] [options]     # options: see `transcribe-pdf.sh --help`
#   transcribe-pdf.sh --test                            # run the unit tests
#
# Env:
#   TRANSCRIBE_PDF_VENV      venv location   (default ~/.cache/transcribe-pdf/venv)
#   TRANSCRIBE_PDF_CACHE     cache location  (default ~/.cache/transcribe-pdf; compiled OCR helper)
#   TRANSCRIBE_PDF_PASSWORD  password tried on encrypted PDFs (--password overrides it for one run)
#   TRANSCRIBE_PDF_ENV_FILE  optional .env loaded first (default ~/.config/transcribe-pdf/.env, chmod 600);
#                         keys: references/.env.example. A variable already set in the shell wins.
#   TRANSCRIBE_PDF_PYTHON    base interpreter used to create the venv (default python3)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${TRANSCRIBE_PDF_ENV_FILE:-$HOME/.config/transcribe-pdf/.env}"

# Load TRANSCRIBE_PDF_* keys from the .env file (parsed, never sourced). A variable already set in the shell wins.
load_env_file() {
    local file="$1" line key val
    [ -f "$file" ] || return 0
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in ''|'#'*) continue ;; esac
        line="${line#export }"
        key="${line%%=*}"
        val="${line#*=}"
        case "$key" in TRANSCRIBE_PDF_*) ;; *) continue ;; esac
        case "$key" in *[!A-Za-z0-9_]*) continue ;; esac
        val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"
        case "$val" in "~/"*) val="$HOME/${val#\~/}" ;; esac    # expand a leading ~/
        if [ -z "${!key+x}" ]; then export "$key=$val"; fi
    done < "$file"
}

load_env_file "$ENV_FILE"      # before reading any other setting, so .env can set them

VENV="${TRANSCRIBE_PDF_VENV:-$HOME/.cache/transcribe-pdf/venv}"
PY_BASE="${TRANSCRIBE_PDF_PYTHON:-python3}"
REQ="$SCRIPT_DIR/requirements.txt"
STAMP="$VENV/.requirements.sha"

ensure_venv() {
    local want
    want="$(shasum -a 256 "$REQ" | cut -d' ' -f1)"
    if [ ! -x "$VENV/bin/python" ]; then
        echo "transcribe-pdf: creating venv in $VENV" >&2
        mkdir -p "$(dirname "$VENV")"
        "$PY_BASE" -m venv "$VENV"
    fi
    if [ ! -f "$STAMP" ] || [ "$(cat "$STAMP")" != "$want" ]; then
        echo "transcribe-pdf: installing requirements" >&2
        "$VENV/bin/python" -m pip install -q --disable-pip-version-check \
            --only-binary=:all: -r "$REQ" >&2
        echo "$want" > "$STAMP"
    fi
}

ensure_venv

if [ "${1:-}" = "--test" ]; then
    cd "$SCRIPT_DIR"
    exec "$VENV/bin/python" -m unittest discover -s "$SCRIPT_DIR" -p 'test_*.py' -v
fi

exec "$VENV/bin/python" "$SCRIPT_DIR/pdf_to_md.py" "$@"
