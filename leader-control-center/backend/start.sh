#!/usr/bin/env bash
# Start the backend API together with Temporal (no frontend).
# Whole stack: ../start.sh. See README.md (Run, Dependencies) for details.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../scripts/start-lib.sh
source "$SCRIPT_DIR/../scripts/start-lib.sh"
TEMPORAL_COMPOSE="$LCC_ROOT/_infra_/docker-temporal/docker-compose.yml"

lcc_load_env

# shell env > .env > defaults; CLI flags win. Temporal is on by default here,
# regardless of WITH_TEMPORAL in .env (that one drives ../start.sh).
PORT="${PORT:-8010}"
HOST="${HOST:-0.0.0.0}"
TEMPORAL_GRPC_PORT="${TEMPORAL_GRPC_PORT:-7233}"
WITH_TEMPORAL=1
KEEP_TEMPORAL=0
SKIP_SYNC=false
RELOAD=true
HEALTH_TIMEOUT_S=180

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Starts Temporal (docker compose, ../_infra_/docker-temporal), then the backend
API. Ctrl+C stops the backend and the Temporal containers this script started.

Options:
    -p, --port PORT       Backend API port (default: 8010)
    -h, --host HOST       Backend bind address (default: 0.0.0.0)
    --no-temporal         Backend only (simulation engine, no Docker)
    --keep-temporal       Leave Temporal running when the backend stops
    --no-reload           Run uvicorn without --reload
    --skip-sync           Skip 'uv sync'
    --help                Show this help message

Environment variables (or backend/.env):
    PORT, HOST, TEMPORAL_GRPC_PORT (default 7233), CORS_ORIGINS, SQLITE_PATH,
    SIMULATION_TICK_SECONDS, SCHEDULER_TICK_SECONDS  (see .env.example)

Examples:
    $0                    # Temporal + backend :8010
    $0 -p 8100            # backend on :8100
    $0 --keep-temporal    # keep Temporal up after Ctrl+C
    $0 --no-temporal      # backend only
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port) lcc_need_value "$@"; PORT="$2"; shift 2 ;;
        -h|--host) lcc_need_value "$@"; HOST="$2"; shift 2 ;;
        --no-temporal) WITH_TEMPORAL=0; shift ;;
        --keep-temporal) KEEP_TEMPORAL=1; shift ;;
        --no-reload) RELOAD=false; shift ;;
        --skip-sync) SKIP_SYNC=true; shift ;;
        --help) usage ;;
        *) echo "Unknown option: $1 (see --help)" >&2; exit 1 ;;
    esac
done

export PORT HOST TEMPORAL_GRPC_PORT
# Allow the vite dev server on its default port unless configured otherwise.
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:$FRONTEND_PORT,http://127.0.0.1:$FRONTEND_PORT}"

BACKEND_PID=""
HEALTH_PID=""
STARTED_TEMPORAL=0

# Fail early, with the reason, when Docker cannot run the Temporal stack.
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "Error: docker not found; Temporal needs Docker. Install it or use --no-temporal." >&2
        exit 1
    fi
    if ! docker info >/dev/null 2>&1; then
        echo "Error: the Docker daemon is not running. Start Docker Desktop, or use --no-temporal." >&2
        exit 1
    fi
}

temporal_health() {
    docker inspect -f '{{.State.Health.Status}}' temporal 2>/dev/null || echo "absent"
}

# Wait for the temporal container to be healthy, then refresh the local API
# snapshot (_api_/temporal, gitignored). Background; never fatal.
await_temporal() {
    local i status
    for ((i = 0; i < HEALTH_TIMEOUT_S / 2; i++)); do
        status="$(temporal_health)"
        if [[ "$status" == "healthy" ]]; then
            echo "Temporal ready: gRPC localhost:$TEMPORAL_GRPC_PORT · UI http://localhost:8080"
            "$SCRIPT_DIR/scripts/temporal-api.sh" refresh >/dev/null \
                || echo "Warning: Temporal API snapshot refresh failed (scripts/temporal-api.sh refresh)." >&2
            return 0
        fi
        sleep 2
    done
    echo "Warning: Temporal not healthy after ${HEALTH_TIMEOUT_S}s (last status: $(temporal_health))." >&2
    echo "  Inspect with:  docker compose -f $TEMPORAL_COMPOSE logs temporal" >&2
}

cleanup() {
    trap - SIGINT SIGTERM EXIT
    echo ""
    echo "Stopping backend..."
    lcc_kill_tree "$BACKEND_PID"
    lcc_kill_tree "$HEALTH_PID"
    # Only stop the containers this run started; a Temporal that was already
    # running (e.g. from ../start.sh) is left alone.
    if [[ "$STARTED_TEMPORAL" == "1" && "$KEEP_TEMPORAL" == "0" ]]; then
        echo "Stopping Temporal..."
        docker compose -f "$TEMPORAL_COMPOSE" down || true
    elif [[ "$WITH_TEMPORAL" == "1" ]]; then
        echo "Temporal left running. Stop it with:"
        echo "  docker compose -f $TEMPORAL_COMPOSE down"
    fi
}

lcc_check_port "$PORT" "Backend"
trap cleanup SIGINT SIGTERM EXIT

if [[ "$WITH_TEMPORAL" == "1" ]]; then
    check_docker
    if [[ "$(temporal_health)" == "healthy" ]]; then
        echo "Temporal already running; reusing it."
    else
        lcc_check_port "$TEMPORAL_GRPC_PORT" "Temporal gRPC"
        echo "Starting Temporal (docker compose)..."
        docker compose -f "$TEMPORAL_COMPOSE" up -d
        STARTED_TEMPORAL=1
    fi
    await_temporal &
    HEALTH_PID=$!
    disown "$HEALTH_PID"  # no job notice when cleanup stops it
fi

cd "$SCRIPT_DIR"
[[ "$SKIP_SYNC" == false ]] && uv sync --quiet

echo "Starting backend on http://localhost:$PORT (API docs: http://localhost:$PORT/api)..."
UVICORN_ARGS=(app.main:app --host "$HOST" --port "$PORT")
[[ "$RELOAD" == true ]] && UVICORN_ARGS+=(--reload)
uv run uvicorn "${UVICORN_ARGS[@]}" &
BACKEND_PID=$!

echo "Press Ctrl+C to stop."
wait "$BACKEND_PID"
