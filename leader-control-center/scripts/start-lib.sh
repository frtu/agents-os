# Shared helpers for ./start.sh, backend/start.sh and frontend/start.sh.
# Source it; do not execute. Bash 3.2 compatible (macOS system bash).

LCC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Load local, uncommitted config from backend/.env (cp backend/.env.example
# backend/.env). It holds the shared ports for both apps. Variables already set
# in the environment win over the file.
lcc_load_env() {
    local env_file="$LCC_ROOT/backend/.env" key value
    [[ -f "$env_file" ]] || return 0
    while IFS='=' read -r key value || [[ -n "$key" ]]; do
        [[ -z "$key" || "$key" == \#* ]] && continue
        [[ -z "${!key+x}" ]] && export "$key=$value"
    done < "$env_file"
    return 0
}

# Refuse to start on a busy port (usually a leftover from a previous run).
lcc_check_port() {
    local port="$1" name="$2" pid
    pid="$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | head -1 || true)"
    if [[ -n "$pid" ]]; then
        echo "Error: $name port $port is already in use by PID $pid ($(ps -o comm= -p "$pid"))." >&2
        echo "  Stop it with:  $LCC_ROOT/stop-kill-port.sh $port   or pick another port (--help)." >&2
        exit 1
    fi
}

# Print a process and all its descendants, children first.
lcc_tree_pids() {
    local pid="$1" child
    for child in $(pgrep -P "$pid" 2>/dev/null); do
        lcc_tree_pids "$child"
    done
    echo "$pid"
}

# Stop a process and all its descendants (uv/npm spawn uvicorn/vite as
# children): SIGTERM, wait up to $2 seconds (default 10) for a graceful exit,
# then SIGKILL whatever is left. Returns only once the whole tree is gone.
lcc_kill_tree() {
    local pid="${1:-}" timeout="${2:-10}" pids p i alive
    [[ -z "$pid" ]] && return 0
    pids="$(lcc_tree_pids "$pid")"
    for p in $pids; do kill "$p" 2>/dev/null || true; done
    for ((i = 0; i < timeout * 4; i++)); do
        alive=""
        for p in $pids; do kill -0 "$p" 2>/dev/null && alive="$alive $p"; done
        [[ -z "$alive" ]] && return 0
        sleep 0.25
    done
    echo "Warning: PID(s)$alive did not exit within ${timeout}s; killing." >&2
    for p in $alive; do kill -9 "$p" 2>/dev/null || true; done
}

# Fail with a clear message when a flag is missing its value.
lcc_need_value() {
    if [[ $# -lt 2 || -z "$2" || "$2" == -* ]]; then
        echo "Error: $1 needs a value (see --help)." >&2
        exit 1
    fi
}
