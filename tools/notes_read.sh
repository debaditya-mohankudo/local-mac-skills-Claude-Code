#!/bin/bash
# Usage: notes_read.sh "TITLE"
# Returns the full plaintext of a note in the "Claude" folder.
TITLE="$1"
osascript -e "tell application \"Notes\"
  tell folder \"Claude\"
    set n to first note whose name is \"$TITLE\"
    return plaintext of n
  end tell
end tell"
