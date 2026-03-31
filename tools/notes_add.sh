#!/bin/bash
# Usage: notes_add.sh "TITLE" "BODY"
# Creates a new note in the "Claude" folder.
TITLE="$1"
BODY="$2"
osascript -e "tell application \"Notes\"
  tell folder \"Claude\"
    make new note with properties {name:\"$TITLE\", body:\"$BODY\"}
  end tell
end tell"
