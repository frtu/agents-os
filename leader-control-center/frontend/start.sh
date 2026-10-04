#!/usr/bin/env bash
# Start the frontend (vite dev server). It proxies /api to the backend, which
# must be started separately (../backend/start.sh) unless VITE_USE_MOCKS=true.
# Whole stack: ../start.sh. See README.md for details.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../scripts/start-lib.sh
source "$SCRIPT_DIR/../scripts/start-lib.sh"

lcc_load_env

# shell env > backend/.env > defaults; CLI flags win.
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_PORT="${BACKEND_PORT:-${PORT:-8010}}"
SKIP_SYNC=false
MIN_NODE_MAJOR=18

usage() {
    cat <<USAGE
Usage: $0 [OPTIONS]

Starts the vite dev server. /api and /openapi.json are proxied to the backend.

Options:
    -f, --port PORT           Frontend dev server port (default: 5173)
    -b, --backend-port PORT   Backend port the dev proxy targets (default: \$PORT or 8010)
    --skip-sync               Skip 'npm install'
    --help                    Show this help message

Environment variables (or ../backend/.env):
    FRONTEND_PORT, BACKEND_PORT (falls back to PORT)
    VITE_USE_MOCKS            true = in-browser mock backend (see .env.example)

Examples:
    $0                        # frontend :5173 -> backend :8010
    $0 -f 5180 -b 8100        # frontend :5180 -> backend :8100
USAGE
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--port) lcc_need_value "$@"; FRONTEND_PORT="$2"; shift 2 ;;
        -b|--backend-port) lcc_need_value "$@"; BACKEND_PORT="$2"; shift 2 ;;
        --skip-sync) SKIP_SYNC=true; shift ;;
        --help) usage ;;
        *) echo "Unknown option: $1 (see --help)" >&2; exit 1 ;;
    esac
done

# vite.config.ts reads both.
export FRONTEND_PORT BACKEND_PORT

# Pick the Node version from .nvmrc via nvm when available, then fail early if
# node is still too old for vite.
use_node() {
    local nvm_sh="${NVM_DIR:-$HOME/.nvm}/nvm.sh" major
    if [[ -s "$nvm_sh" && -f "$SCRIPT_DIR/.nvmrc" ]]; then
        # nvm.sh is not written for `set -u`.
        set +u
        # shellcheck disable=SC1090
        source "$nvm_sh"
        nvm use "$(cat "$SCRIPT_DIR/.nvmrc")" >/dev/null 2>&1 || true
        set -u
    fi
    major="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
    if (( major < MIN_NODE_MAJOR )); then
        echo "Error: Node >= $MIN_NODE_MAJOR required for the frontend (found: $(node -v 2>/dev/null || echo none))." >&2
        echo "  Install it with nvm:  nvm install $(cat "$SCRIPT_DIR/.nvmrc" 2>/dev/null || echo 20)" >&2
        exit 1
    fi
}

FRONTEND_PID=""

cleanup() {
    trap - SIGINT SIGTERM EXIT
    echo ""
    echo "Stopping frontend..."
    lcc_kill_tree "$FRONTEND_PID"
}

use_node
lcc_check_port "$FRONTEND_PORT" "Frontend"
trap cleanup SIGINT SIGTERM EXIT

cd "$SCRIPT_DIR"
[[ "$SKIP_SYNC" == false ]] && npm install --silent

echo "Starting frontend on http://localhost:$FRONTEND_PORT (proxy -> backend :$BACKEND_PORT)..."
npm run dev &
FRONTEND_PID=$!

wait "$FRONTEND_PID"
