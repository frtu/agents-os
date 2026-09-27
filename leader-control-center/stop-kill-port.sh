#!/bin/bash
# Kill process running on the backend port
# Usage: ./stop-kill-port.sh [PORT]   (default: $PORT or 8010)

PORT="${1:-${PORT:-8010}}"
PID=$(lsof -t -i :$PORT)

if [ -z "$PID" ]; then
    echo "No process found on port $PORT"
    exit 0
fi

echo "Killing process $PID on port $PORT"
kill -9 $PID

if [ $? -eq 0 ]; then
    echo "Process killed successfully"
else
    echo "Failed to kill process"
    exit 1
fi
