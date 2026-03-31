#!/bin/bash
# Usage: calendar_add_event.sh CALENDAR TITLE START END [NOTES]
# Adds a new event to the given calendar.
# Date format: "MM/DD/YYYY HH:MM:SS"
CALENDAR="$1"
TITLE="$2"
START="$3"
END="$4"
NOTES="${5:-}"
osascript << EOF
tell application "Calendar"
  tell calendar "$CALENDAR"
    make new event with properties {summary:"$TITLE", start date:date "$START", end date:date "$END", description:"$NOTES"}
  end tell
end tell
EOF
