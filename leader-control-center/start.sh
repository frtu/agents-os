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

cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    if [[ "$WITH_TEMPORAL" == "1" ]]; then
        docker compose -f "$TEMPORAL_COMPOSE" down || true
    fi
    exit 0
}

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
echo "  Backend:  http://localhost:$PORT (API docs: http://localhost:$PORT/docs)"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
if [[ "$WITH_TEMPORAL" == "1" ]]; then
    echo "  Temporal: localhost:7233 (UI: http://localhost:8080)"
fi
echo ""
echo "Press Ctrl+C to stop all services"

wait
