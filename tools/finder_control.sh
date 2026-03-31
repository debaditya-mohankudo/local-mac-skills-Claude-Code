#!/bin/bash
# Usage: finder_control.sh COMMAND [PATH]
# Commands:
#   open PATH     — open a file or folder in Finder
#   reveal PATH   — reveal and select an item in its parent folder
#   mkdir PATH    — create a new folder and reveal it in Finder (HOME subtree only)
#   trash PATH    — move a file or folder to Trash (requires y/N confirmation)

COMMAND="$1"
TARGET="$2"

case "$COMMAND" in
  open)
    if [[ -z "$TARGET" ]]; then
      echo "Usage: finder_control.sh open PATH"
      exit 1
    fi
    if [[ ! -e "$TARGET" ]]; then
      echo "ERROR: Path does not exist: $TARGET"
      exit 1
    fi
    osascript -e "tell application \"Finder\" to open (POSIX file \"$TARGET\" as alias)"
    osascript -e 'tell application "Finder" to activate'
    echo "Opened: $TARGET"
    ;;
  reveal)
    if [[ -z "$TARGET" ]]; then
      echo "Usage: finder_control.sh reveal PATH"
      exit 1
    fi
    if [[ ! -e "$TARGET" ]]; then
      echo "ERROR: Path does not exist: $TARGET"
      exit 1
    fi
    osascript -e "tell application \"Finder\" to reveal (POSIX file \"$TARGET\" as alias)"
    osascript -e 'tell application "Finder" to activate'
    echo "Revealed: $TARGET"
    ;;
  mkdir)
    if [[ -z "$TARGET" ]]; then
      echo "Usage: finder_control.sh mkdir PATH"
      exit 1
    fi
    # Restrict to HOME subtree to avoid creating directories in system paths
    REAL_TARGET=$(realpath -m "$TARGET" 2>/dev/null || echo "$TARGET")
    if [[ "$REAL_TARGET" != "$HOME"* ]]; then
      echo "ERROR: mkdir is restricted to paths within \$HOME ($HOME)."
      exit 1
    fi
    mkdir -p "$TARGET"
    osascript -e "tell application \"Finder\" to reveal (POSIX file \"$TARGET\" as alias)"
    osascript -e 'tell application "Finder" to activate'
    echo "Created: $TARGET"
    ;;
  trash)
    if [[ -z "$TARGET" ]]; then
      echo "Usage: finder_control.sh trash PATH"
      exit 1
    fi
    if [[ ! -e "$TARGET" ]]; then
      echo "ERROR: Path does not exist: $TARGET"
      exit 1
    fi
    echo "Move to Trash: $TARGET"
    printf "Are you sure? [y/N] "
    read -r CONFIRM
    if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
      echo "Aborted."
      exit 0
    fi
    osascript -e "tell application \"Finder\" to delete (POSIX file \"$TARGET\" as alias)"
    echo "Moved to Trash: $TARGET"
    ;;
  quit-apps)
    echo "Listing running apps..."
    APP_NAMES=$(osascript -e '
      tell application "System Events"
        set theNames to name of every application process whose background only is false and name is not in {"Code", "Finder", "SystemUIServer"}
        set output to ""
        repeat with n in theNames
          set output to output & n & linefeed
        end repeat
        return output
      end tell
    ' 2>/dev/null)

    while IFS= read -r appName; do
      [[ -z "$appName" ]] && continue
      echo "Quitting: $appName"
      osascript -e "
        tell application \"System Events\"
          set theProc to first application process whose name is \"$appName\"
          quit theProc
        end tell
      " 2>/dev/null
      sleep 1
    done <<< "$APP_NAMES"

    echo "Done — all apps closed (VSCode and Finder kept alive)."
    ;;
  *)
    echo "Usage: finder_control.sh open|reveal|mkdir|trash|quit-apps PATH"
    exit 1
    ;;
esac
