#!/bin/bash
# Usage: contacts_search.sh "NAME" [--with-email]
# Searches macOS Contacts by name. Pass --with-email to include email addresses.
NAME="$1"
WITH_EMAIL="$2"

if [ "$WITH_EMAIL" = "--with-email" ]; then
  osascript << EOF
tell application "Contacts"
  set results to every person whose name contains "$NAME"
  set output to ""
  repeat with p in results
    set pName to name of p
    repeat with ph in phones of p
      set output to output & pName & " | phone | " & (label of ph) & ": " & (value of ph) & "\n"
    end repeat
    repeat with em in emails of p
      set output to output & pName & " | email | " & (label of em) & ": " & (value of em) & "\n"
    end repeat
  end repeat
  return output
end tell
EOF
else
  osascript << EOF
tell application "Contacts"
  set results to every person whose name contains "$NAME"
  set output to ""
  repeat with p in results
    set pName to name of p
    repeat with ph in phones of p
      set output to output & pName & " | " & (label of ph) & ": " & (value of ph) & "\n"
    end repeat
  end repeat
  return output
end tell
EOF
fi
