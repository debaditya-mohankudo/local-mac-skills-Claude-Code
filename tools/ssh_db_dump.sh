#!/bin/bash
# Usage: ssh_db_dump.sh USER@IP [CONTAINER] [DB_NAME] [DB_USER] [DB_TYPE]
# Dumps a Postgres or MySQL database from a remote Docker container to LOG_CACHE_DIR.
# Falls back to ssh_config.sh defaults for any omitted arguments.

HOST="$1"
if [[ -z "$HOST" ]]; then
  echo "Usage: ssh_db_dump.sh USER@IP [CONTAINER] [DB_NAME] [DB_USER] [DB_TYPE]"
  exit 1
fi

source "$(dirname "$0")/ssh_common.sh"

CONFIG="$HOME/workspace/claude_for_mac_local/ssh_config.sh"
LOG_CACHE_DIR="/tmp/claude"
DB_CONTAINER=""
DB_NAME=""
DB_USER=""
DB_TYPE="mysql"
[[ -f "$CONFIG" ]] && source "$CONFIG"
check_allowed_host "$HOST" || exit 1

CONTAINER="${2:-$DB_CONTAINER}"
NAME="${3:-$DB_NAME}"
USER="${4:-$DB_USER}"
TYPE="${5:-$DB_TYPE}"

if [[ -z "$CONTAINER" || -z "$NAME" || -z "$USER" ]]; then
  echo "Missing required DB config. Provide as arguments or set DB_CONTAINER, DB_NAME, DB_USER in ssh_config.sh."
  exit 1
fi

mkdir -p "$LOG_CACHE_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SAFE_HOST="${HOST//[@\/]/_}"
OUTFILE="$LOG_CACHE_DIR/${SAFE_HOST}_${CONTAINER}_${NAME}_dump_${TIMESTAMP}.sql"

echo "Dumping $TYPE database '$NAME' from container '$CONTAINER' on $HOST..."

case "$TYPE" in
  postgres|pg)
    ssh "${SSH_OPTS[@]}" "$HOST" "docker exec $CONTAINER pg_dump -U $USER $NAME" > "$OUTFILE" 2>&1
    ;;
  mysql)
    ssh "${SSH_OPTS[@]}" "$HOST" "docker exec $CONTAINER mysqldump -u $USER $NAME" > "$OUTFILE" 2>&1
    ;;
  *)
    echo "Unknown DB_TYPE '$TYPE'. Use 'mysql' or 'postgres'."
    exit 1
    ;;
esac

LINES=$(wc -l < "$OUTFILE")
SIZE=$(du -sh "$OUTFILE" | cut -f1)
echo "Dump complete — $LINES lines, $SIZE"
echo "Cached: $OUTFILE"
