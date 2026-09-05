#!/usr/bin/env bash
# Startup script for Leader Assistant
# See getting-started.md for full documentation

set -e

# Default configuration
PORT="${LEADER_PORT:-8000}"
HOST="${LEADER_HOST:-127.0.0.1}"

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
    -p, --port PORT     Set server port (default: 8000)
    -h, --host HOST     Set server host (default: 127.0.0.1)
    --skip-sync         Skip 'uv sync' dependency install
    --help              Show this help message

Environment variables:
    LEADER_PORT              Server port
    LEADER_HOST              Server host
    LEADER_VAULT_ROOT        Folder holding Vaults/<name>/ (default: ./Vaults)
    LEADER_VAULT_PATH        Point at one specific vault directory
    LEADER_DEFAULT_VAULT     Default vault name (default: default)

Examples:
    $0                       # Start on default port 8000
    $0 -p 8080               # Start on port 8080
    $0 --skip-sync           # Skip dependency sync
EOF
    exit 0
}

SKIP_SYNC=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        --skip-sync)
            SKIP_SYNC=true
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

cd "$(dirname "$0")"

# Load environment file if it exists
if [[ -f .env ]]; then
    set -a
    source .env
    set +a
fi

# Install dependencies
if [[ "$SKIP_SYNC" == false ]]; then
    echo "Installing dependencies..."
    uv sync
fi

# Export environment
export LEADER_PORT="$PORT"
export LEADER_HOST="$HOST"

echo ""
echo "Starting Leader Assistant on http://${HOST}:${PORT}/"
echo ""

# Run the server
exec uv run app
