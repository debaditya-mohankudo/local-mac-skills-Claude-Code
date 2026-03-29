#!/bin/bash
# Usage: reminders_list.sh [STATUS]
# Lists all reminders. STATUS: all (default), pending, completed.
STATUS="${1:-all}"
osascript << EOF
tell application "Reminders"
  set output to ""
  repeat with l in every list
    set lName to name of l
    repeat with r in every reminder of l
      set rCompleted to completed of r
      -- filter by status
      if "$STATUS" is "pending" and rCompleted is true then
      else if "$STATUS" is "completed" and rCompleted is false then
      else
        set rName to name of r
        set rDue to ""
        set rNotes to ""
        try
          if due date of r is not missing value then set rDue to due date of r as string
        end try
        try
          if body of r is not missing value and body of r is not "" then set rNotes to body of r
        end try
        set output to output & lName & "\t" & rName & "\t" & rCompleted & "\t" & rDue & "\t" & rNotes & "\n"
      end if
    end repeat
  end repeat
  return output
end tell
EOF
