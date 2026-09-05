#!/bin/bash
# Kill process running on port 8000

PORT=8000
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
