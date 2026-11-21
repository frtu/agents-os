#!/bin/bash
# pdf-extract.sh — entry point. Bootstraps a private venv, then runs the orchestrator.
#
# Usage:
#   pdf-extract.sh <file-or-dir> [...] [options]     # options: see `pdf-extract.sh --help`
#   pdf-extract.sh --test                            # run the unit tests
#
# Env:
#   PDF_EXTRACT_VENV      venv location   (default ~/.cache/pdf-extract/venv)
#   PDF_EXTRACT_CACHE     cache location  (default ~/.cache/pdf-extract; compiled OCR helper)
#   PDF_EXTRACT_PASSWORD  password tried on encrypted PDFs (--password overrides it for one run)
#   PDF_EXTRACT_ENV_FILE  optional .env loaded first (default ~/.config/pdf-extract/.env, chmod 600);
#                         keys: references/.env.example. A variable already set in the shell wins.
#   PDF_EXTRACT_PYTHON    base interpreter used to create the venv (default python3)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${PDF_EXTRACT_ENV_FILE:-$HOME/.config/pdf-extract/.env}"

# Load PDF_EXTRACT_* keys from the .env file (parsed, never sourced). A variable already set in the shell wins.
load_env_file() {
    local file="$1" line key val
    [ -f "$file" ] || return 0
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in ''|'#'*) continue ;; esac
        line="${line#export }"
        key="${line%%=*}"
        val="${line#*=}"
        case "$key" in PDF_EXTRACT_*) ;; *) continue ;; esac
        case "$key" in *[!A-Za-z0-9_]*) continue ;; esac
        val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"
        case "$val" in "~/"*) val="$HOME/${val#\~/}" ;; esac    # expand a leading ~/
        if [ -z "${!key+x}" ]; then export "$key=$val"; fi
    done < "$file"
}

load_env_file "$ENV_FILE"      # before reading any other setting, so .env can set them

VENV="${PDF_EXTRACT_VENV:-$HOME/.cache/pdf-extract/venv}"
PY_BASE="${PDF_EXTRACT_PYTHON:-python3}"
REQ="$SCRIPT_DIR/requirements.txt"
STAMP="$VENV/.requirements.sha"

ensure_venv() {
    local want
    want="$(shasum -a 256 "$REQ" | cut -d' ' -f1)"
    if [ ! -x "$VENV/bin/python" ]; then
        echo "pdf-extract: creating venv in $VENV" >&2
        mkdir -p "$(dirname "$VENV")"
        "$PY_BASE" -m venv "$VENV"
    fi
    if [ ! -f "$STAMP" ] || [ "$(cat "$STAMP")" != "$want" ]; then
        echo "pdf-extract: installing requirements" >&2
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
