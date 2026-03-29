#!/bin/bash
# Usage: ssh_db_query.sh USER@IP "SQL QUERY" [CONTAINER] [DB_NAME] [DB_USER]
# Runs a MySQL query inside a remote Docker container using a read-only connection.
# Caches the result to LOG_CACHE_DIR. Falls back to ssh_config.sh defaults for omitted arguments.

HOST="$1"
QUERY="$2"
if [[ -z "$HOST" || -z "$QUERY" ]]; then
  echo "Usage: ssh_db_query.sh USER@IP \"SQL QUERY\" [CONTAINER] [DB_NAME] [DB_USER]"
  exit 1
fi

# Guardrail: block destructive SQL before anything else — no SSH, no config needed
QUERY_UPPER=$(echo "$QUERY" | tr '[:lower:]' '[:upper:]')
for keyword in DROP ALTER TRUNCATE DELETE RENAME CREATE REPLACE; do
  if echo "$QUERY_UPPER" | grep -qw "$keyword"; then
    echo "BLOCKED: '$keyword' is not allowed. Only read queries (SELECT, SHOW, DESCRIBE, EXPLAIN) are permitted."
    exit 1
  fi
done

source "$(dirname "$0")/ssh_common.sh"

CONFIG="$HOME/workspace/claude_for_mac_local/ssh_config.sh"
LOG_CACHE_DIR="/tmp/claude"
DB_CONTAINER=""
DB_NAME=""
DB_USER=""
DB_READONLY_USER=""
[[ -f "$CONFIG" ]] && source "$CONFIG"
check_allowed_host "$HOST" || exit 1

CONTAINER="${3:-$DB_CONTAINER}"
NAME="${4:-$DB_NAME}"
# Prefer the read-only user if configured, fall back to DB_USER
USER="${5:-${DB_READONLY_USER:-$DB_USER}}"

if [[ -z "$CONTAINER" || -z "$NAME" || -z "$USER" ]]; then
  echo "Missing required DB config. Provide as arguments or set DB_CONTAINER, DB_NAME, DB_USER in ssh_config.sh."
  exit 1
fi

mkdir -p "$LOG_CACHE_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SAFE_HOST="${HOST//[@\/]/_}"
OUTFILE="$LOG_CACHE_DIR/${SAFE_HOST}_${CONTAINER}_query_${TIMESTAMP}.txt"

echo "Query: $QUERY" > "$OUTFILE"
echo "---" >> "$OUTFILE"

ssh "${SSH_OPTS[@]}" "$HOST" "docker exec $CONTAINER mysql -u $USER --read-only $NAME -e \"$QUERY\"" >> "$OUTFILE" 2>&1

echo "=== Result ==="
cat "$OUTFILE"
echo "==="
echo "Cached: $OUTFILE"
