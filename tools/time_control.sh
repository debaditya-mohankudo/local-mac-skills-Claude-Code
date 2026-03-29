#!/usr/bin/env bash
# time_control.sh — get current time, set an alarm, or wait N minutes
# Usage:
#   time_control.sh now
#   time_control.sh alarm <HH:MM> [label]
#   time_control.sh wait <minutes> [label]

set -euo pipefail

CMD="${1:-now}"

_notify() {
  local title="$1"
  local msg="$2"
  osascript -e "display notification \"$msg\" with title \"$title\" sound name \"Glass\""
}

_alert() {
  local title="$1"
  local msg="$2"
  osascript -e "display alert \"$title\" message \"$msg\""
}

case "$CMD" in

  now)
    echo "Current time: $(date '+%A, %d %b %Y  %H:%M:%S %Z')"
    ;;

  alarm)
    # alarm [--reminder] HH:MM [label]
    USE_REMINDER=false
    ALARM_ARGS=("${@:2}")  # everything after "alarm"

    if [[ "${ALARM_ARGS[0]:-}" == "--reminder" ]]; then
      USE_REMINDER=true
      ALARM_ARGS=("${ALARM_ARGS[@]:1}")
    fi

    TARGET="${ALARM_ARGS[0]:-}"
    LABEL="${ALARM_ARGS[1]:-Alarm}"

    if [[ -z "$TARGET" ]]; then
      echo "Usage: time_control.sh alarm [--reminder] HH:MM [label]" >&2
      exit 1
    fi

    # Validate HH:MM
    if ! [[ "$TARGET" =~ ^([01]?[0-9]|2[0-3]):[0-5][0-9]$ ]]; then
      echo "Invalid time format. Use HH:MM (24-hour)." >&2
      exit 1
    fi

    NOW_EPOCH=$(date +%s)
    TARGET_EPOCH=$(date -j -f "%H:%M" "$TARGET" "+%s" 2>/dev/null || true)

    # If target is in the past (before now), schedule for tomorrow
    if [[ "$TARGET_EPOCH" -le "$NOW_EPOCH" ]]; then
      TARGET_EPOCH=$(( TARGET_EPOCH + 86400 ))
    fi

    HUMAN=$(date -r "$TARGET_EPOCH" '+%H:%M on %a %d %b')

    # Schedule via `at` using exact clock time — survives terminal close
    AT_CMD="osascript -e 'display notification \"Alarm: $TARGET\" with title \"⏰ ${LABEL}\" sound name \"Glass\"'; osascript -e 'display alert \"⏰ ${LABEL}\" message \"It is now $TARGET\"'"
    echo "$AT_CMD" | at "$TARGET" 2>&1

    # Optionally also create an Apple Reminder (persists across reboots + syncs to iPhone)
    if [[ "$USE_REMINDER" == true ]]; then
      DUE_DATE=$(date -r "$TARGET_EPOCH" '+%m/%d/%Y %H:%M:%S')
      ~/workspace/claude_for_mac_local/tools/reminders_add.sh "Reminders" "⏰ ${LABEL}" "$DUE_DATE"
      echo "Alarm set: \"$LABEL\" at $HUMAN (scheduled via at + Apple Reminder)"
    else
      echo "Alarm set: \"$LABEL\" at $HUMAN (scheduled via at)"
    fi
    ;;

  wait)
    # wait <minutes> [label]
    MINUTES="${2:-}"
    LABEL="${3:-Timer}"

    if [[ -z "$MINUTES" ]]; then
      echo "Usage: time_control.sh wait <minutes> [label]" >&2
      exit 1
    fi

    if ! [[ "$MINUTES" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
      echo "Invalid minutes. Must be a positive number." >&2
      exit 1
    fi

    # Round to nearest whole minute for `at` (minimum 1)
    AT_MINS=$(awk "BEGIN {m=int($MINUTES + 0.5); print (m < 1 ? 1 : m)}")
    FINISH=$(date -v "+${AT_MINS}M" '+%H:%M')

    # Schedule via `at` — survives terminal close, managed by launchd atrun
    AT_CMD="osascript -e 'display notification \"${MINUTES} min elapsed\" with title \"⏱ ${LABEL}\" sound name \"Glass\"'; osascript -e 'display alert \"⏱ ${LABEL}\" message \"${MINUTES} minute(s) are up!\"'"
    echo "$AT_CMD" | at "now + ${AT_MINS} minutes" 2>&1

    echo "Timer started: \"$LABEL\" — ${MINUTES} min, finishes ~$FINISH (scheduled via at)"
    ;;

  *)
    echo "Unknown command: $CMD" >&2
    echo "Usage: time_control.sh now | alarm HH:MM [label] | wait <minutes> [label]" >&2
    exit 1
    ;;
esac
