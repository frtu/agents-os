#!/bin/bash
# Start both backend and frontend for Leader Control Center

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Starting Leader Control Center..."

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
echo ""
echo "Press Ctrl+C to stop all services"

wait
