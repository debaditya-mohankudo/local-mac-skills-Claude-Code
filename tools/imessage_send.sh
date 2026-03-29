#!/bin/bash
# Usage: imessage_send.sh [-y] [--delay MINUTES] RECIPIENT MESSAGE
# Sends an iMessage to a phone number or Apple ID email.
# Without -y, prints a preview and exits (dry-run).
# Pass -y to confirm and actually send.
# Pass --delay MINUTES to schedule send after N minutes (runs in background).

CONFIRM=0
DELAY=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y)
      CONFIRM=1
      shift
      ;;
    --delay)
      DELAY="$2"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

RECIPIENT="$1"
MESSAGE="$2"

if [[ -z "$RECIPIENT" || -z "$MESSAGE" ]]; then
  echo "Usage: imessage_send.sh [-y] [--delay MINUTES] RECIPIENT MESSAGE" >&2
  exit 1
fi

if [[ "$CONFIRM" -ne 1 ]]; then
  echo "DRY RUN — message not sent."
  echo "  To: $RECIPIENT"
  echo "  Message: $MESSAGE"
  if [[ -n "$DELAY" ]]; then
    echo "  Delay: $DELAY minutes"
  fi
  echo "Re-run with -y to send."
  exit 0
fi

# Check if ALLOWED_PHONE_NUMBERS is set (load from .env if exists)
if [[ -z "$ALLOWED_PHONE_NUMBERS" && -f ".env" ]]; then
  source ".env" 2>/dev/null
fi

# Validate recipient against allowed list if configured
if [[ -n "$ALLOWED_PHONE_NUMBERS" ]]; then
  # Convert comma-separated list to array and trim whitespace
  IFS=',' read -ra ALLOWED_ARRAY <<< "$ALLOWED_PHONE_NUMBERS"
  FOUND=0
  for allowed in "${ALLOWED_ARRAY[@]}"; do
    # Trim whitespace
    allowed=$(echo "$allowed" | xargs)
    if [[ "$RECIPIENT" == "$allowed" ]]; then
      FOUND=1
      break
    fi
  done
  if [[ $FOUND -eq 0 ]]; then
    echo "Error: Recipient '$RECIPIENT' is not in ALLOWED_PHONE_NUMBERS" >&2
    exit 1
  fi
fi

# Helper function to send the message
send_message() {
  osascript -e "tell application \"Messages\"
    set targetService to 1st service whose service type = iMessage
    set targetBuddy to buddy \"$RECIPIENT\" of targetService
    send \"$MESSAGE\" to targetBuddy
  end tell"
}

# If delay is specified, run in background
if [[ -n "$DELAY" ]]; then
  (
    # Convert minutes to seconds (handle both integer and decimal)
    SECONDS=$(printf "%.0f" "$(echo "$DELAY * 60" | bc 2>/dev/null || python3 -c "print(int($DELAY * 60))")")
    sleep "$SECONDS"
    send_message
  ) &
else
  send_message
fi
