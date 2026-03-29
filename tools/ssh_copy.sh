#!/bin/bash
# Usage: ssh_copy.sh USER@IP LOCAL_SRC REMOTE_DEST
# Copies a local file to a remote directory over SCP.
# LOCAL_SRC  — any local file path, no restriction.
# REMOTE_DEST — validated against REMOTE_DIRS in ssh_config.sh.
#               Accepts nickname:path syntax (e.g. "app:logs/") or full absolute path.

HOST="$1"
LOCAL_SRC="$2"
REMOTE_DEST="$3"

if [[ -z "$HOST" || -z "$LOCAL_SRC" || -z "$REMOTE_DEST" ]]; then
  echo "Usage: ssh_copy.sh USER@IP LOCAL_SRC REMOTE_DEST"
  echo "  LOCAL_SRC   — any local file path"
  echo "  REMOTE_DEST — nickname:dir (e.g. app:logs/) or full path"
  exit 1
fi

source "$(dirname "$0")/ssh_common.sh"

CONFIG="$HOME/workspace/claude_for_mac_local/ssh_config.sh"
DISABLE_DIR_RESTRICTION=false
REMOTE_DIRS=("tmp=/tmp")
[[ -f "$CONFIG" ]] && source "$CONFIG"
check_allowed_host "$HOST" || exit 1

# Resolve remote nickname:subpath or full path against REMOTE_DIRS
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

LOCAL_PATH="$LOCAL_SRC"
REMOTE_PATH=$(resolve_remote "$REMOTE_DEST") || exit 1

if [[ ! -f "$LOCAL_PATH" ]]; then
  echo "ERROR: Local file not found: $LOCAL_PATH"
  exit 1
fi

# Guardrail: warn if file already exists on remote
REMOTE_FILE="$REMOTE_PATH/$(basename "$LOCAL_PATH")"
EXISTS=$(ssh "${SSH_OPTS[@]}" "$HOST" "test -f '$REMOTE_FILE' && echo yes || echo no" 2>/dev/null)
if [[ "$EXISTS" == "yes" ]]; then
  echo "WARNING: $REMOTE_FILE already exists on remote."
  echo "Overwrite? [y/N]"
  read -r CONFIRM
  [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]] && echo "Aborted." && exit 0
fi

scp "${SCP_OPTS[@]}" "$LOCAL_PATH" "$HOST:$REMOTE_PATH"

echo "Copied: $LOCAL_PATH → $HOST:$REMOTE_PATH"
