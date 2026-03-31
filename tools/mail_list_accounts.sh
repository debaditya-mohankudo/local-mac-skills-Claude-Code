#!/bin/bash
# Usage: mail_list_accounts.sh
# Lists all accounts in macOS Mail with their email addresses.
osascript << 'EOF'
tell application "Mail"
  set output to ""
  repeat with acct in accounts
    set output to output & (name of acct) & " | " & (email addresses of acct as string) & "\n"
  end repeat
  return output
end tell
EOF
