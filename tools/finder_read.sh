#!/bin/bash
# Usage: finder_read.sh COMMAND
# Commands:
#   front-path    — POSIX path of the front Finder window's target folder
#   list-windows  — list all open Finder windows and their paths
#   selection     — POSIX paths of all currently selected items

COMMAND="${1:-front-path}"

case "$COMMAND" in
  front-path)
    osascript -e '
      tell application "Finder"
        if (count of windows) is 0 then
          return "No Finder windows open"
        end if
        return POSIX path of (target of front window as alias)
      end tell'
    ;;
  list-windows)
    osascript -e '
      tell application "Finder"
        set winCount to count of windows
        if winCount is 0 then return "No Finder windows open"
        set output to ""
        repeat with i from 1 to winCount
          try
            set p to POSIX path of (target of window i as alias)
          on error
            set p to "(special view)"
          end try
          set output to output & "Window " & i & ": " & p & "\n"
        end repeat
        return output
      end tell'
    ;;
  selection)
    osascript -e '
      tell application "Finder"
        set sel to selection
        if sel is {} then return "Nothing selected"
        set output to ""
        repeat with f in sel
          set output to output & POSIX path of (f as alias) & "\n"
        end repeat
        return output
      end tell'
    ;;
  list-apps)
    osascript -e '
      tell application "System Events"
        set theNames to name of every application process whose background only is false
        set output to ""
        repeat with n in theNames
          set output to output & n & linefeed
        end repeat
        return output
      end tell'
    ;;
  *)
    echo "Usage: finder_read.sh front-path|list-windows|selection|list-apps"
    exit 1
    ;;
esac
