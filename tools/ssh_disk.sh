#!/bin/bash
# Usage: ssh_disk.sh USER@IP
# Fetches disk usage report from a remote host and caches it to LOG_CACHE_DIR.

HOST="$1"
if [[ -z "$HOST" ]]; then
  echo "Usage: ssh_disk.sh USER@IP"
  exit 1
fi

source "$(dirname "$0")/ssh_common.sh"

CONFIG="$HOME/workspace/claude_for_mac_local/ssh_config.sh"
LOG_CACHE_DIR="/tmp/claude"
[[ -f "$CONFIG" ]] && source "$CONFIG"
check_allowed_host "$HOST" || exit 1

mkdir -p "$LOG_CACHE_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SAFE_HOST="${HOST//[@\/]/_}"
OUTFILE="$LOG_CACHE_DIR/${SAFE_HOST}_disk_${TIMESTAMP}.txt"

ssh "${SSH_OPTS[@]}" "$HOST" bash <<'REMOTE' > "$OUTFILE" 2>&1
echo "=== Disk usage (df -h) ==="
df -h

echo ""
echo "=== Top directories by size (/) ==="
du -sh /* 2>/dev/null | sort -rh | head -20

echo ""
echo "=== Docker volumes ==="
docker system df 2>/dev/null || echo "Docker not available"
REMOTE

echo "=== Preview ==="
head -20 "$OUTFILE"
echo "==="
echo "Cached: $OUTFILE"
