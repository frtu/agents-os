#!/usr/bin/env bash
# Start both backend and frontend for Leader Control Center
# See backend/README.md (Configuration, Dependencies) for full documentation

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPORAL_COMPOSE="$SCRIPT_DIR/../docker/temporal/docker-compose.yml"

# Load local, uncommitted config (copy backend/.env.example to backend/.env).
# Variables already set in the shell win over the file.
if [[ -f "$SCRIPT_DIR/backend/.env" ]]; then
    while IFS='=' read -r key value; do
        [[ -z "$key" || "$key" == \#* ]] && continue
        [[ -z "${!key+x}" ]] && export "$key=$value"
    done < "$SCRIPT_DIR/backend/.env"
fi

# Default configuration (shell env > backend/.env > defaults; CLI flags win)
PORT="${PORT:-8010}"
HOST="${HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
WITH_TEMPORAL="${WITH_TEMPORAL:-0}"
SKIP_SYNC=false

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
    -p, --port PORT            Backend API port (default: 8010)
    -h, --host HOST            Backend bind address (default: 0.0.0.0)
    -f, --frontend-port PORT   Frontend dev server port (default: 5173)
    --temporal                 Also start Temporal docker compose (../docker/temporal)
                               and stop it again on Ctrl+C
    --skip-sync                Skip 'uv sync' / 'npm install'
    --help                     Show this help message

Environment variables (or backend/.env):
    PORT, HOST, FRONTEND_PORT, WITH_TEMPORAL=1, CORS_ORIGINS, SQLITE_PATH,
    SIMULATION_TICK_SECONDS  (see backend/.env.example)

Examples:
    $0                         # Backend :8010, frontend :5173
    $0 -p 8100 -f 5180         # Backend :8100, frontend :5180
    $0 --temporal              # Also start Temporal
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port) PORT="$2"; shift 2 ;;
        -h|--host) HOST="$2"; shift 2 ;;
        -f|--frontend-port) FRONTEND_PORT="$2"; shift 2 ;;
        --temporal) WITH_TEMPORAL=1; shift ;;
        --skip-sync) SKIP_SYNC=true; shift ;;
        --help) usage ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# The backend reads PORT/HOST/CORS_ORIGINS; vite reads BACKEND_PORT/FRONTEND_PORT.
export PORT HOST FRONTEND_PORT
export BACKEND_PORT="$PORT"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:$FRONTEND_PORT,http://127.0.0.1:$FRONTEND_PORT}"

MIN_NODE_MAJOR=18

# Pick the Node version from frontend/.nvmrc via nvm when available, then
# fail early if node is still too old for vite.
use_node() {
    local nvm_sh="${NVM_DIR:-$HOME/.nvm}/nvm.sh"
    if [[ -s "$nvm_sh" && -f "$SCRIPT_DIR/frontend/.nvmrc" ]]; then
        # shellcheck disable=SC1090
        source "$nvm_sh"
        nvm use "$(cat "$SCRIPT_DIR/frontend/.nvmrc")" >/dev/null 2>&1 || true
    fi
    local major
    major="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
    if (( major < MIN_NODE_MAJOR )); then
        echo "Error: Node >= $MIN_NODE_MAJOR required for the frontend (found: $(node -v 2>/dev/null || echo none))." >&2
        echo "  Install it with nvm:  nvm install $(cat "$SCRIPT_DIR/frontend/.nvmrc" 2>/dev/null || echo 20)" >&2
        exit 1
    fi
}

# Refuse to start on a busy port (usually a leftover from a previous run).
check_port() {
    local port="$1" name="$2" pid
    pid="$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | head -1)"
    if [[ -n "$pid" ]]; then
        echo "Error: $name port $port is already in use by PID $pid ($(ps -o comm= -p "$pid"))." >&2
        echo "  Stop it with:  ./stop-kill-port.sh $port   or pick another port (--help)." >&2
        exit 1
    fi
}

# Kill a process and all its descendants (uv/npm spawn uvicorn/vite as children).
kill_tree() {
    local pid="$1" child
    [[ -z "$pid" ]] && return
    for child in $(pgrep -P "$pid" 2>/dev/null); do
        kill_tree "$child"
    done
    kill "$pid" 2>/dev/null || true
}

cleanup() {
    trap - SIGINT SIGTERM
    echo "Stopping services..."
    kill_tree "$BACKEND_PID"
    kill_tree "$FRONTEND_PID"
    if [[ "$WITH_TEMPORAL" == "1" ]]; then
        docker compose -f "$TEMPORAL_COMPOSE" down || true
    fi
    exit 0
}

use_node
check_port "$PORT" "Backend"
check_port "$FRONTEND_PORT" "Frontend"

trap cleanup SIGINT SIGTERM

echo "Starting Leader Control Center..."

# Start Temporal (optional)
if [[ "$WITH_TEMPORAL" == "1" ]]; then
    echo "Starting Temporal (docker compose)..."
    docker compose -f "$TEMPORAL_COMPOSE" up -d
fi

# Start backend
echo "Starting backend on http://localhost:$PORT..."
cd "$SCRIPT_DIR/backend"
[[ "$SKIP_SYNC" == false ]] && uv sync --quiet
uv run uvicorn app.main:app --reload --host "$HOST" --port "$PORT" &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend on http://localhost:$FRONTEND_PORT..."
cd "$SCRIPT_DIR/frontend"
[[ "$SKIP_SYNC" == false ]] && npm install --silent
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Services running:"
echo "  Backend:  http://localhost:$PORT (API docs: http://localhost:$PORT/api)"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
if [[ "$WITH_TEMPORAL" == "1" ]]; then
    echo "  Temporal: localhost:7233 (UI: http://localhost:8080)"
fi
echo ""
echo "Press Ctrl+C to stop all services"

wait
