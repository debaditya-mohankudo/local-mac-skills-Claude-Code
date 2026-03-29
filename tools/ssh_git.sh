#!/bin/bash
# Usage: ssh_git.sh USER@IP "GIT COMMAND" [REPO]
# Runs git commands on a remote repository.
# REPO accepts a nickname (from REMOTE_DIRS in ssh_config.sh) or a full path.
# Subdirectories of configured REMOTE_DIRS are automatically allowed.
# Write/destructive commands require explicit user confirmation before running.

HOST="$1"
GIT_CMD="$2"
REPO="${3:-}"

if [[ -z "$HOST" || -z "$GIT_CMD" ]]; then
  echo "Usage: ssh_git.sh USER@IP \"GIT COMMAND\" [REPO]"
  echo "  GIT COMMAND — e.g. \"log --oneline -10\", \"status\", \"diff HEAD~1\""
  echo "  REPO        — nickname (e.g. app) or full path. Uses first GIT_DIRS entry if omitted."
  exit 1
fi

source "$(dirname "$0")/ssh_common.sh"

CONFIG="$HOME/workspace/claude_for_mac_local/ssh_config.sh"
LOG_CACHE_DIR="/tmp/claude"
REMOTE_DIRS=()
[[ -f "$CONFIG" ]] && source "$CONFIG"
check_allowed_host "$HOST" || exit 1

# Detect write/destructive git subcommands
WRITE_CMDS=(
  commit push pull merge rebase reset checkout fetch add rm mv
  "stash pop" "stash apply" "stash drop" "stash clear"
  "branch -d" "branch -D" "branch -m"
  "tag -d" "tag -a" "tag -f"
  "remote add" "remote remove" "remote set-url"
  clean restore "submodule update" cherry-pick revert
  "gc" "prune" init clone
)

CMD_LOWER=$(echo "$GIT_CMD" | tr '[:upper:]' '[:lower:]' | xargs)
NEEDS_CONFIRM=false
for write_cmd in "${WRITE_CMDS[@]}"; do
  if [[ "$CMD_LOWER" == "$write_cmd"* || "$CMD_LOWER" == *" $write_cmd "* ]]; then
    NEEDS_CONFIRM=true
    break
  fi
done

if [[ "$NEEDS_CONFIRM" == "true" ]]; then
  echo "WARNING: 'git $GIT_CMD' is a write/destructive operation on $HOST:$REPO_PATH"
  printf "Run on remote? [y/N] "
  read -r CONFIRM
  if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Aborted."
    exit 0
  fi
fi

# Resolve repo path — nickname or full path, must be within REMOTE_DIRS or a subdir
resolve_repo() {
  local input="$1"

  if [[ -z "$input" ]]; then
    if [[ ${#REMOTE_DIRS[@]} -eq 0 ]]; then
      echo "ERROR: No REMOTE_DIRS configured in ssh_config.sh and no REPO provided." >&2
      return 1
    fi
    # Default to first entry
    echo "${REMOTE_DIRS[0]#*=}"
    return 0
  fi

  # Nickname lookup
  for entry in "${REMOTE_DIRS[@]}"; do
    if [[ "${entry%%=*}" == "$input" ]]; then
      echo "${entry#*=}"
      return 0
    fi
  done

  # Full path — must be within a configured REMOTE_DIR or its subdirectory
  for entry in "${REMOTE_DIRS[@]}"; do
    local base="${entry#*=}"
    if [[ "$input" == "$base" || "$input" == "$base/"* ]]; then
      echo "$input"
      return 0
    fi
  done

  echo "ERROR: '$input' is not a known nickname or within a configured REMOTE_DIR." >&2
  echo "Add it to REMOTE_DIRS in ssh_config.sh." >&2
  return 1
}

REPO_PATH=$(resolve_repo "$REPO") || exit 1

mkdir -p "$LOG_CACHE_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SAFE_HOST="${HOST//[@\/]/_}"
SAFE_CMD=$(echo "$GIT_CMD" | tr ' /' '__' | tr -cd '[:alnum:]_-' | cut -c1-30)
OUTFILE="$LOG_CACHE_DIR/${SAFE_HOST}_git_${SAFE_CMD}_${TIMESTAMP}.txt"

echo "# git $GIT_CMD" > "$OUTFILE"
echo "# repo: $REPO_PATH" >> "$OUTFILE"
echo "---" >> "$OUTFILE"

ssh "${SSH_OPTS[@]}" "$HOST" "cd '$REPO_PATH' && git $GIT_CMD" >> "$OUTFILE" 2>&1

echo "=== git $GIT_CMD ==="
cat "$OUTFILE"
echo "==="
echo "Cached: $OUTFILE"
