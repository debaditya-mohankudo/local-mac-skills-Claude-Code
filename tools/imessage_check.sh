#!/bin/bash
# Usage: imessage_check.sh [MINUTES] [CONTACT]
# Reads iMessages from the last N minutes (default: 30).
# Optionally filter by phone number or contact name (e.g., imessage_check.sh 30 Simraan).
# If no contact provided, loads IMESSAGE_PHONE_NUMBER from .env
# Requires Full Disk Access for the terminal app.

# Load .env if it exists (from project root)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "$PROJECT_ROOT/.env" ]; then
  export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

MINUTES="${1:-30}"
CONTACT="${2:-${IMESSAGE_PHONE_NUMBER:-}}"

# Function to resolve contact name to phone numbers
resolve_contact() {
  local contact_input="$1"

  # Check if it looks like a phone number (all digits, +, or -)
  if [[ "$contact_input" =~ ^[+0-9-]*$ ]]; then
    # It's a phone number, return as-is
    echo "$contact_input"
  else
    # It's a contact name, look it up in Contacts
    local phone_numbers=$("$PROJECT_ROOT/tools/contacts_search.sh" "$contact_input" | sed -n 's/.*: \(.*\)/\1/p' | head -1 | tr -d ' ')
    if [ -n "$phone_numbers" ]; then
      echo "$phone_numbers"
    else
      echo ""
    fi
  fi
}

PHONE_NUMBER=$(resolve_contact "$CONTACT")

# Function to get messages
get_messages() {
  if [ -z "$PHONE_NUMBER" ]; then
    sqlite3 ~/Library/Messages/chat.db "
SELECT
  datetime(message.date/1000000000 + strftime('%s','2001-01-01'), 'unixepoch', 'localtime') AS time,
  CASE WHEN message.is_from_me = 1 THEN 'Me' ELSE COALESCE(handle.id, 'Unknown') END AS sender,
  COALESCE(message.text, '[Media/Attachment]') AS message_text
FROM message
LEFT JOIN handle ON message.handle_id = handle.ROWID
WHERE message.date >= (strftime('%s', datetime('now', '-$MINUTES minutes')) - strftime('%s', '2001-01-01')) * 1000000000
ORDER BY message.date ASC;
"
  else
    sqlite3 ~/Library/Messages/chat.db "
SELECT
  datetime(message.date/1000000000 + strftime('%s','2001-01-01'), 'unixepoch', 'localtime') AS time,
  CASE WHEN message.is_from_me = 1 THEN 'Me' ELSE COALESCE(handle.id, 'Unknown') END AS sender,
  COALESCE(message.text, '[Media/Attachment]') AS message_text
FROM message
LEFT JOIN handle ON message.handle_id = handle.ROWID
WHERE handle.id IN ('$PHONE_NUMBER', '+91$PHONE_NUMBER', '+1$PHONE_NUMBER')
ORDER BY message.date ASC;
"
  fi
}

echo "📬 Messages:"
echo ""
get_messages
