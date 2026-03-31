#!/bin/bash
# Usage: calendar_delete_event.sh CALENDAR "EXACT TITLE"
CALENDAR="$1"
TITLE="$2"
osascript << EOF
tell application "Calendar"
  tell calendar "$CALENDAR"
    set matchEvt to first event whose summary is "$TITLE"
    delete matchEvt
  end tell
end tell
EOF
