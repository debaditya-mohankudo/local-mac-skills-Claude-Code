#!/bin/bash
# Usage: calendar_list_events.sh "START_DATE" "END_DATE"
# Lists calendar events between two dates (AppleScript date string format: "MM/DD/YYYY HH:MM:SS").
START="$1"
END="$2"
osascript << EOF
tell application "Calendar"
  set output to ""
  set startDate to date "$START"
  set endDate to date "$END"
  set skipList to {"Birthdays", "Siri Suggestions", "Vedic Astro Events"}
  repeat with c in every calendar
    set cName to name of c
    if skipList does not contain cName then
      set evts to every event of c whose start date >= startDate and start date <= endDate
      repeat with e in evts
        set eNotes to ""
        try
          if description of e is not missing value then set eNotes to description of e
        end try
        set output to output & cName & "\t" & (summary of e) & "\t" & ((start date of e) as string) & "\t" & ((end date of e) as string) & "\t" & eNotes & "\n"
      end repeat
    end if
  end repeat
  return output
end tell
EOF
