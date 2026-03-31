#!/bin/bash
# Usage: ssh_fetch.sh USER@IP REMOTE_SRC
# Fetches a file from a remote host to LOG_CACHE_DIR (/tmp/claude by default).
# REMOTE_SRC accepts nickname:path syntax (e.g. "app:logs/error.log")
# or a full absolute path (validated against REMOTE_DIRS in ssh_config.sh).

HOST="$1"
REMOTE_SRC="$2"

if [[ -z "$HOST" || -z "$REMOTE_SRC" ]]; then
  echo "Usage: ssh_fetch.sh USER@IP REMOTE_SRC"
  echo "  REMOTE_SRC — nickname:file (e.g. tmp:app.log) or full path"
  exit 1
fi

source "$(dirname "$0")/ssh_common.sh"

CONFIG="$HOME/workspace/claude_for_mac_local/ssh_config.sh"
LOG_CACHE_DIR="/tmp/claude"
DISABLE_DIR_RESTRICTION=false
REMOTE_DIRS=("tmp=/tmp")
[[ -f "$CONFIG" ]] && source "$CONFIG"
check_allowed_host "$HOST" || exit 1

mkdir -p "$LOG_CACHE_DIR"

# Resolve nickname:subpath or full path against REMOTE_DIRS
resolve_remote() {
  local input="$1"

  if [[ "$DISABLE_DIR_RESTRICTION" == "true" ]]; then
    echo "$input"
    return 0
  fi

  if [[ "$input" == *":"* ]]; then
    local nick="${input%%:*}"
    local rest="${input#*:}"
    for entry in "${REMOTE_DIRS[@]}"; do
      if [[ "${entry%%=*}" == "$nick" ]]; then
        echo "${entry#*=}/$rest"
        return 0
      fi
    done
    echo "ERROR: Unknown remote nickname '$nick'. Add it to REMOTE_DIRS in ssh_config.sh." >&2
    return 1
  else
    for entry in "${REMOTE_DIRS[@]}"; do
      local base="${entry#*=}"
      if [[ "$input" == "$base"* ]]; then
        echo "$input"
        return 0
      fi
    done
    echo "ERROR: '$input' is not within an allowed remote directory. Add it to REMOTE_DIRS in ssh_config.sh." >&2
    return 1
  fi
}

REMOTE_PATH=$(resolve_remote "$REMOTE_SRC") || exit 1

FILENAME=$(basename "$REMOTE_PATH")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SAFE_HOST="${HOST//[@\/]/_}"
OUTFILE="$LOG_CACHE_DIR/${SAFE_HOST}_${FILENAME%.*}_${TIMESTAMP}.${FILENAME##*.}"

# Handle files with no extension
[[ "$FILENAME" != *.* ]] && OUTFILE="$LOG_CACHE_DIR/${SAFE_HOST}_${FILENAME}_${TIMESTAMP}"

scp "${SCP_OPTS[@]}" "$HOST:$REMOTE_PATH" "$OUTFILE"

echo "Fetched: $HOST:$REMOTE_PATH → $OUTFILE"
