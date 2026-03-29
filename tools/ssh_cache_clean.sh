#!/bin/bash
# Usage: ssh_cache_clean.sh [DAYS]
# Deletes files in LOG_CACHE_DIR older than DAYS days (default: CACHE_RETENTION_DAYS from config).

CONFIG="$HOME/workspace/claude_for_mac_local/ssh_config.sh"
LOG_CACHE_DIR="/tmp/claude"
CACHE_RETENTION_DAYS=7
[[ -f "$CONFIG" ]] && source "$CONFIG"

DAYS="${1:-$CACHE_RETENTION_DAYS}"

if [[ ! -d "$LOG_CACHE_DIR" ]]; then
  echo "Cache directory $LOG_CACHE_DIR does not exist. Nothing to clean."
  exit 0
fi

DELETED=$(find "$LOG_CACHE_DIR" -maxdepth 1 -type f -mtime +"$DAYS" -print -delete)

if [[ -z "$DELETED" ]]; then
  echo "No files older than $DAYS days found in $LOG_CACHE_DIR."
else
  echo "Deleted:"
  echo "$DELETED"
  COUNT=$(echo "$DELETED" | wc -l | tr -d ' ')
  echo "--- $COUNT file(s) removed from $LOG_CACHE_DIR"
fi
