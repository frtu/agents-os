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
#   PDF_EXTRACT_PASSWORD  extra password tried on encrypted PDFs
#   PDF_EXTRACT_PYTHON    base interpreter used to create the venv (default python3)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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
