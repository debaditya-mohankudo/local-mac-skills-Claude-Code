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

# Check if recipient is allowed in the contacts database
DB_PATH="$HOME/Documents/claude_cache_data/personal_contacts.sqlite"
if [[ -f "$DB_PATH" ]]; then
  # Query: check if contact exists and is allowed (by phone OR email)
  IS_ALLOWED=$(sqlite3 "$DB_PATH" "SELECT allowed FROM contacts WHERE (phone = '$RECIPIENT' OR email = '$RECIPIENT') AND allowed = 'y' LIMIT 1;" 2>/dev/null)

  if [[ -z "$IS_ALLOWED" ]]; then
    # Try to get the contact name for a better error message
    CONTACT_NAME=$(sqlite3 "$DB_PATH" "SELECT name FROM contacts WHERE phone = '$RECIPIENT' OR email = '$RECIPIENT' LIMIT 1;" 2>/dev/null)
    if [[ -n "$CONTACT_NAME" ]]; then
      echo "Error: Recipient '$CONTACT_NAME' ($RECIPIENT) is not allowed to receive messages. Set allowed='y' in contacts database." >&2
    else
      echo "Error: Recipient '$RECIPIENT' is not in allowed contacts. Add to contacts database with allowed='y'." >&2
    fi
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
