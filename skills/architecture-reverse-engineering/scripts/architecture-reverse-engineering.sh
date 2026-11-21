#!/bin/bash
# architecture-reverse-engineering.sh — entry point. Stdlib-only Python, no venv: dispatches
# to the scan (evidence) or the check (gate on the generated doc).
#
# Usage:
#   architecture-reverse-engineering.sh scan  <repo> [--json] [options]   # see: scan --help
#   architecture-reverse-engineering.sh check <doc.md> [--repo <root>] [--json]   # see: check --help
#   architecture-reverse-engineering.sh --test                             # run the unit tests
#
# Env:
#   ARCHITECTURE_REVERSE_ENGINEERING_PYTHON         interpreter (default python3)
#   ARCHITECTURE_REVERSE_ENGINEERING_SIGNALS_LOCAL  local signals overlay
#       (default ~/.config/architecture-reverse-engineering/signals.local.json if it exists)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${ARCHITECTURE_REVERSE_ENGINEERING_PYTHON:-python3}"

usage() {
    sed -n '2,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

command -v "$PY" >/dev/null || {
    echo "architecture-reverse-engineering: $PY not found — install Python 3.9+ or set ARCHITECTURE_REVERSE_ENGINEERING_PYTHON" >&2
    exit 2
}

case "${1:-}" in
    scan)
        shift
        exec "$PY" "$SCRIPT_DIR/scan_repo.py" "$@"
        ;;
    check)
        shift
        exec "$PY" "$SCRIPT_DIR/check_diagram.py" "$@"
        ;;
    --test)
        cd "$SCRIPT_DIR"
        exec "$PY" -m unittest discover -s "$SCRIPT_DIR" -p 'test_*.py' -v
        ;;
    -h|--help)
        usage
        exit 0
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac
