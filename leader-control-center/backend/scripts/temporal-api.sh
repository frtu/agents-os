#!/usr/bin/env bash
# Call or snapshot the Temporal gRPC API via server reflection.
# See ../dependencies.md. Requires Temporal running (../start.sh or docker compose).
#
#   scripts/temporal-api.sh refresh                 # regenerate _api_/temporal/*
#   scripts/temporal-api.sh list [SERVICE]          # services / methods
#   scripts/temporal-api.sh describe SYMBOL         # rpc or message definition
#   scripts/temporal-api.sh call METHOD [JSON]      # invoke, e.g. ListNamespaces '{}'
#
# Uses a local grpcurl against localhost:$TEMPORAL_GRPC_PORT when installed,
# otherwise the fullstorydev/grpcurl image on the temporal-network.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="$SCRIPT_DIR/../_api_/temporal"
WF=temporal.api.workflowservice.v1.WorkflowService
SERVICES=(
    temporal.api.workflowservice.v1.WorkflowService
    temporal.api.operatorservice.v1.OperatorService
    temporal.server.api.adminservice.v1.AdminService
)

if command -v grpcurl >/dev/null 2>&1; then
    ADDR="localhost:${TEMPORAL_GRPC_PORT:-7233}"
    grpc() { grpcurl -plaintext "$@"; }
else
    ADDR="temporal:7233"
    grpc() { docker run --rm -i --network temporal-network fullstorydev/grpcurl -plaintext "$@"; }
fi

# Short method names (e.g. ListNamespaces) default to WorkflowService.
qualify() { [[ "$1" == *.* || "$1" == */* ]] && echo "$1" || echo "$WF/$1"; }

refresh() {
    mkdir -p "$OUT_DIR"
    local version
    version="$(grpc -d '{}' "$ADDR" "$WF/GetSystemInfo" | sed -n 's/.*"serverVersion": "\(.*\)".*/\1/p')"
    grpc "$ADDR" list > "$OUT_DIR/services.txt"
    for svc in "${SERVICES[@]}"; do
        grpc "$ADDR" describe "$svc" > "$OUT_DIR/${svc##*.}.txt"
    done
    echo "temporal server $version, refreshed $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$OUT_DIR/VERSION"
    echo "Wrote $OUT_DIR ($(cat "$OUT_DIR/VERSION"))"
}

cmd="${1:-}"; shift || true
case "$cmd" in
    refresh) refresh ;;
    list) grpc "$ADDR" list "$@" ;;
    describe) grpc "$ADDR" describe "$1" ;;
    call) body="${2:-}"; [[ -z "$body" ]] && body="{}"; grpc -d "$body" "$ADDR" "$(qualify "$1")" ;;
    *) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
