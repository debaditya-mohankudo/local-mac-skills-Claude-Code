#!/bin/bash
# Usage: mail_fetch_inbox.sh ACCOUNT_NAME [N]
# Fetches the last N emails from the INBOX of the given Mail account (default: 5).
ACCOUNT="$1"
N="${2:-5}"
osascript << EOF
tell application "Mail"
  set output to ""
  set acctInbox to mailbox "INBOX" of account "$ACCOUNT"
  set inboxMsgs to messages of acctInbox
  set msgCount to count of inboxMsgs
  if msgCount > $N then set msgCount to $N
  repeat with i from 1 to msgCount
    set m to item i of inboxMsgs
    set readStatus to ""
    if read status of m is false then set readStatus to " [UNREAD]"
    set output to output & i & ". " & (sender of m) & " | " & (subject of m) & " | " & ((date received of m) as string) & readStatus & "\n"
  end repeat
  return output
end tell
EOF
