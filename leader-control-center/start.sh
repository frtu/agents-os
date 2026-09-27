#!/bin/bash
# Start both backend and frontend for Leader Control Center
#
# Usage: ./start.sh [--temporal]
#   --temporal   also start the Temporal docker compose (../docker/temporal)
#                and stop it again on Ctrl+C. Same as WITH_TEMPORAL=1.

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPORAL_COMPOSE="$SCRIPT_DIR/../docker/temporal/docker-compose.yml"
WITH_TEMPORAL="${WITH_TEMPORAL:-0}"

for arg in "$@"; do
    case "$arg" in
        --temporal) WITH_TEMPORAL=1 ;;
        -h|--help) sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Unknown option: $arg" >&2; exit 1 ;;
    esac
done

cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    if [ "$WITH_TEMPORAL" = "1" ]; then
        docker compose -f "$TEMPORAL_COMPOSE" down || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Starting Leader Control Center..."

# Start Temporal (optional)
if [ "$WITH_TEMPORAL" = "1" ]; then
    echo "Starting Temporal (docker compose)..."
    docker compose -f "$TEMPORAL_COMPOSE" up -d
fi

# Start backend
echo "Starting backend on http://localhost:8000..."
cd "$SCRIPT_DIR/backend"
uv sync --quiet
uv run uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend on http://localhost:5173..."
cd "$SCRIPT_DIR/frontend"
npm install --silent
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Services running:"
echo "  Backend:  http://localhost:8000 (API docs: http://localhost:8000/docs)"
echo "  Frontend: http://localhost:5173"
if [ "$WITH_TEMPORAL" = "1" ]; then
    echo "  Temporal: localhost:7233 (UI: http://localhost:8080)"
fi
echo ""
echo "Press Ctrl+C to stop all services"

wait
