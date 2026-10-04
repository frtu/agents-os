#!/usr/bin/env bash
# Start the whole Leader Control Center stack by running backend/start.sh
# (API + optional Temporal) and frontend/start.sh (vite) side by side.
# Each script owns its own setup and cleanup; this one only coordinates them.
# See backend/README.md (Configuration, Dependencies) for full documentation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/start-lib.sh
source "$SCRIPT_DIR/scripts/start-lib.sh"

lcc_load_env

# shell env > backend/.env > defaults; CLI flags win.
PORT="${PORT:-8010}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
WITH_TEMPORAL="${WITH_TEMPORAL:-1}"
BACKEND_ARGS=()
FRONTEND_ARGS=()

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Runs backend/start.sh and frontend/start.sh together; Ctrl+C stops both.
If either one exits, the other is stopped too.

Options:
    -p, --port PORT            Backend API port (default: 8010)
    -h, --host HOST            Backend bind address (default: 0.0.0.0)
    -f, --frontend-port PORT   Frontend dev server port (default: 5173)
    --temporal                 Also start Temporal (default: on, or WITH_TEMPORAL)
    --no-temporal              Do not start Temporal
    --keep-temporal            Leave Temporal running after Ctrl+C
    --skip-sync                Skip 'uv sync' / 'npm install'
    --help                     Show this help message

Environment variables (or backend/.env):
    PORT, HOST, FRONTEND_PORT, WITH_TEMPORAL=1, TEMPORAL_GRPC_PORT (default 7233),
    CORS_ORIGINS, SQLITE_PATH, SIMULATION_TICK_SECONDS  (see backend/.env.example)

Each part can also run alone: backend/start.sh --help, frontend/start.sh --help.

Examples:
    $0                         # Backend :8010 (+ Temporal), frontend :5173
    $0 -p 8100 -f 5180         # Backend :8100, frontend :5180
    $0 --no-temporal           # Skip Temporal
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port) lcc_need_value "$@"; PORT="$2"; shift 2 ;;
        -h|--host) lcc_need_value "$@"; BACKEND_ARGS+=(--host "$2"); shift 2 ;;
        -f|--frontend-port) lcc_need_value "$@"; FRONTEND_PORT="$2"; shift 2 ;;
        --temporal) WITH_TEMPORAL=1; shift ;;
        --no-temporal) WITH_TEMPORAL=0; shift ;;
        --keep-temporal) BACKEND_ARGS+=(--keep-temporal); shift ;;
        --skip-sync) BACKEND_ARGS+=(--skip-sync); FRONTEND_ARGS+=(--skip-sync); shift ;;
        --help) usage ;;
        *) echo "Unknown option: $1 (see --help)" >&2; exit 1 ;;
    esac
done

[[ "$WITH_TEMPORAL" == "1" ]] || BACKEND_ARGS+=(--no-temporal)
BACKEND_ARGS+=(--port "$PORT")
FRONTEND_ARGS+=(--port "$FRONTEND_PORT" --backend-port "$PORT")

# The backend derives CORS_ORIGINS from FRONTEND_PORT.
export FRONTEND_PORT

# Fail fast, before anything starts, if either port is taken.
lcc_check_port "$PORT" "Backend"
lcc_check_port "$FRONTEND_PORT" "Frontend"

BACKEND_PID=""
FRONTEND_PID=""

# Background jobs of a script ignore SIGINT, so Ctrl+C reaches this script only;
# forward SIGTERM to each child script and let it run its own cleanup (stopping
# uvicorn/vite and, for the backend, the Temporal containers it started).
stop_children() {
    trap - SIGINT SIGTERM
    local pid
    for pid in "$BACKEND_PID" "$FRONTEND_PID"; do
        [[ -n "$pid" ]] && kill -TERM "$pid" 2>/dev/null || true
    done
    for pid in "$BACKEND_PID" "$FRONTEND_PID"; do
        [[ -n "$pid" ]] && wait "$pid" 2>/dev/null || true
    done
}

on_signal() {
    echo ""
    echo "Stopping services..."
    stop_children
    exit 0
}
trap on_signal SIGINT SIGTERM

echo "Starting Leader Control Center..."
"$SCRIPT_DIR/backend/start.sh" ${BACKEND_ARGS[@]+"${BACKEND_ARGS[@]}"} &
BACKEND_PID=$!
"$SCRIPT_DIR/frontend/start.sh" ${FRONTEND_ARGS[@]+"${FRONTEND_ARGS[@]}"} &
FRONTEND_PID=$!

echo ""
echo "Services:"
echo "  Backend:  http://localhost:$PORT (API docs: http://localhost:$PORT/api)"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
if [[ "$WITH_TEMPORAL" == "1" ]]; then
    echo "  Temporal: gRPC localhost:${TEMPORAL_GRPC_PORT:-7233} (UI: http://localhost:8080)"
fi
echo ""
echo "Press Ctrl+C to stop all services"

# Bash 3.2 has no `wait -n`: poll until either side exits, then stop the other.
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
    sleep 1
done
if kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Frontend stopped; stopping backend..." >&2
else
    echo "Backend stopped; stopping frontend..." >&2
fi
stop_children
exit 1
