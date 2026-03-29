#!/bin/bash
# Usage: reminders_delete.sh LIST "EXACT NAME"
LIST="$1"
NAME="$2"
osascript -e "tell application \"Reminders\"
  set r to first reminder of list \"$LIST\" whose name is \"$NAME\"
  delete r
end tell"
