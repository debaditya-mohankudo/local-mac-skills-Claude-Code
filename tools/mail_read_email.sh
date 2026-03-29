#!/bin/bash
# Usage: mail_read_email.sh ACCOUNT_NAME INDEX
# Reads the full content of email at position INDEX in the account's INBOX.
ACCOUNT="$1"
INDEX="$2"
osascript << EOF
tell application "Mail"
  set acctInbox to mailbox "INBOX" of account "$ACCOUNT"
  set m to item $INDEX of (messages of acctInbox)
  return "From: " & (sender of m) & "\nSubject: " & (subject of m) & "\nDate: " & ((date received of m) as string) & "\n\n" & (content of m)
end tell
EOF
