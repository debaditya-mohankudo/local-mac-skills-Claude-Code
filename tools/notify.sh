#!/bin/bash
# Usage: notify.sh [--list-notifications [HOURS]] [--clear] TITLE MESSAGE [--sound SOUND_NAME]
# Creates macOS notifications and manages notification log
# SOUND_NAME options: Ping, Basso, Blow, Bottle, Frog, Funk, Glass, Hero, Morse, Pop, Submarine, Tink
# Or use --sound none to disable sound

NOTIFY_LOG="$HOME/.claude/notifications.jsonl"
SOUND="Ping"
ACTION="create"
HOURS=24

# Ensure log directory exists
mkdir -p "$HOME/.claude"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --list-notifications)
      ACTION="list"
      if [[ $# -gt 1 && "$2" =~ ^[0-9]+$ ]]; then
        HOURS="$2"
        shift 2
      else
        shift
      fi
      ;;
    --clear)
      ACTION="clear"
      shift
      ;;
    --sound)
      SOUND="$2"
      shift 2
      ;;
    *)
      if [[ "$ACTION" == "create" ]]; then
        TITLE="$1"
        MESSAGE="$2"
        shift 2
      else
        shift
      fi
      ;;
  esac
done

# Function to list notifications
list_notifications() {
  local hours=$1
  local cutoff_time=$(($(date +%s) - (hours * 3600)))

  if [[ ! -f "$NOTIFY_LOG" ]]; then
    echo "No notifications logged yet."
    return 0
  fi

  # Read and filter notifications
  local found=0
  while IFS= read -r line; do
    if [[ -z "$line" ]]; then continue; fi

    # Extract timestamp from JSON
    local timestamp=$(echo "$line" | grep -o '"timestamp":"[^"]*' | cut -d'"' -f4)
    local epoch=$(date -j -f "%Y-%m-%d %H:%M:%S" "$timestamp" +%s 2>/dev/null || echo 0)

    if [[ $epoch -gt $cutoff_time ]]; then
      local app=$(echo "$line" | grep -o '"app":"[^"]*' | cut -d'"' -f4)
      local title=$(echo "$line" | grep -o '"title":"[^"]*' | cut -d'"' -f4)
      local message=$(echo "$line" | grep -o '"message":"[^"]*' | cut -d'"' -f4)

      if [[ $found -eq 0 ]]; then
        printf "%-19s | %-35s | %s\n" "Time" "Title" "Message"
        printf "%s\n" "$(printf '%.0s=' {1..100})"
        found=1
      fi

      printf "[%s] %-35s | %s\n" "$timestamp" "$title" "$message"
    fi
  done < "$NOTIFY_LOG"

  if [[ $found -eq 0 ]]; then
    echo "No notifications in the last $hours hour(s)."
  fi
}

# Function to clear notifications log
clear_notifications() {
  if [[ -f "$NOTIFY_LOG" ]]; then
    rm "$NOTIFY_LOG"
    echo "Notification log cleared."
  else
    echo "No notification log to clear."
  fi
}

# Function to log a notification
log_notification() {
  local title="$1"
  local message="$2"
  local app="${3:-Claude}"

  # Create JSON entry
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  local json_entry="{\"timestamp\":\"$timestamp\",\"app\":\"$app\",\"title\":\"${title//\"/\\\"}\",\"message\":\"${message//\"/\\\"}\"}";

  echo "$json_entry" >> "$NOTIFY_LOG"
}

# Function to create notification
create_notification() {
  local title="$1"
  local message="$2"
  local sound="$3"

  if [[ -z "$title" || -z "$message" ]]; then
    echo "Usage: notify.sh TITLE MESSAGE [--sound SOUND_NAME]" >&2
    return 1
  fi

  # Escape quotes
  local title_esc="${title//\"/\\\"}"
  local message_esc="${message//\"/\\\"}"

  # Send notification
  if [[ "$sound" == "none" ]]; then
    osascript -e "display notification \"$message_esc\" with title \"$title_esc\"" || return 1
  else
    osascript -e "display notification \"$message_esc\" with title \"$title_esc\" sound name \"$sound\"" || return 1
  fi

  # Log the notification
  log_notification "$title" "$message" "Claude"

  return 0
}

# Execute action
case "$ACTION" in
  list)
    list_notifications "$HOURS"
    ;;
  clear)
    clear_notifications
    ;;
  create)
    create_notification "$TITLE" "$MESSAGE" "$SOUND"
    ;;
  *)
    echo "Invalid action" >&2
    exit 1
    ;;
esac

exit $?
