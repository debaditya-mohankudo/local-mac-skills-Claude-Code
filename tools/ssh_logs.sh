#!/bin/bash
# Usage: ssh_logs.sh USER@IP CONTAINER_NAME [TAIL_LINES]
# Fetches docker logs from a remote host and caches them to LOG_CACHE_DIR.

HOST="$1"
CONTAINER="$2"
TAIL="${3:-50}"

if [[ -z "$HOST" || -z "$CONTAINER" ]]; then
  echo "Usage: ssh_logs.sh USER@IP CONTAINER_NAME [TAIL_LINES]"
  exit 1
fi

source "$(dirname "$0")/ssh_common.sh"

# Load config for LOG_CACHE_DIR
CONFIG="$HOME/workspace/claude_for_mac_local/ssh_config.sh"
LOG_CACHE_DIR="/tmp/claude"
if [[ -f "$CONFIG" ]]; then
  source "$CONFIG"
fi
check_allowed_host "$HOST" || exit 1

mkdir -p "$LOG_CACHE_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SAFE_HOST="${HOST//[@\/]/_}"
OUTFILE="$LOG_CACHE_DIR/${SAFE_HOST}_${CONTAINER}_tail${TAIL}_${TIMESTAMP}.log"

ssh "${SSH_OPTS[@]}" "$HOST" "docker logs --tail $TAIL $CONTAINER" > "$OUTFILE" 2>&1

echo "=== Preview (first 10 lines) ==="
head -10 "$OUTFILE"
echo "==="
echo "Cached: $OUTFILE"
