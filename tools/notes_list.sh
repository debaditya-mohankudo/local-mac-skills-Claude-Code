#!/bin/bash
# Usage: notes_list.sh
# Lists all notes in the "Claude" folder with modification date and body preview.
osascript << 'EOF'
tell application "Notes"
  set output to ""
  repeat with n in every note in folder "Claude"
    set nName to name of n
    set nMod to modification date of n as string
    set nBody to plaintext of n
    if length of nBody > 120 then set nBody to (text 1 thru 120 of nBody) & "..."
    set output to output & nName & "\t" & nMod & "\t" & nBody & "\n"
  end repeat
  return output
end tell
EOF
