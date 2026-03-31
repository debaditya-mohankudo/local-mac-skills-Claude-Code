#!/bin/bash
# Usage: notes_delete.sh "EXACT TITLE"
# Deletes a note from the "Claude" folder.
TITLE="$1"
osascript -e "tell application \"Notes\"
  tell folder \"Claude\"
    set matchNote to first note whose name is \"$TITLE\"
    delete matchNote
  end tell
end tell"
