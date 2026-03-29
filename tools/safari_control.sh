#!/bin/bash
# Usage: safari_control.sh COMMAND [VALUE]
# Commands: open, navigate, current-url, current-title, list-tabs, close-tab, close-all-tabs, reload, back, forward, screenshot

COMMAND="$1"
VALUE="$2"

case "$COMMAND" in
  open|navigate)
    if [[ -z "$VALUE" ]]; then
      echo "Usage: safari_control.sh $COMMAND URL"
      exit 1
    fi
    source "$HOME/workspace/claude_for_mac_local/safari_config.sh"
    if [[ "$DISABLE_ALLOWLIST" != "true" ]]; then
      # Extract hostname: strip scheme, path, query, port, and www. prefix
      host="${VALUE#*://}"
      host="${host%%/*}"
      host="${host%%\?*}"
      host="${host%%:*}"
      host="${host#www.}"
      ALLOWED=no
      for domain in "${ALLOWED_URLS[@]}"; do
        domain="${domain#www.}"
        if [[ "$host" == "$domain" || "$host" == *".$domain" ]]; then
          ALLOWED=yes
          break
        fi
      done
      if [[ "$ALLOWED" != "yes" ]]; then
        echo "BLOCKED: '$VALUE' is not in the Safari allowlist (safari_config.sh)."
        echo "To allow it, add the domain to ALLOWED_URLS, or set DISABLE_ALLOWLIST=true (not recommended)."
        exit 1
      fi
    fi
    if [[ "$COMMAND" == "navigate" ]]; then
      # Navigate in the current tab (reuse existing tab)
      osascript -e "tell application \"Safari\" to set URL of current tab of front window to \"$VALUE\""
    else
      # open: open a new tab (original behaviour)
      osascript -e "tell application \"Safari\" to open location \"$VALUE\""
    fi
    osascript -e 'tell application "Safari" to activate'
    echo "Navigated: $VALUE"
    ;;
  current-url)
    osascript -e 'tell application "Safari" to return URL of current tab of front window'
    ;;
  current-title)
    osascript -e 'tell application "Safari" to return name of current tab of front window'
    ;;
  list-tabs)
    osascript -e '
      tell application "Safari"
        set output to ""
        set winIdx to 0
        repeat with w in windows
          set winIdx to winIdx + 1
          set tabIdx to 0
          repeat with t in tabs of w
            set tabIdx to tabIdx + 1
            set output to output & "Window " & winIdx & " Tab " & tabIdx & ": " & name of t & " — " & URL of t & "\n"
          end repeat
        end repeat
        return output
      end tell'
    ;;
  close-tab)
    osascript -e 'tell application "Safari" to close current tab of front window'
    echo "Closed current tab"
    ;;
  close-all-tabs)
    osascript -e 'tell application "Safari" to close every tab of every window'
    echo "Closed all tabs"
    ;;
  reload)
    osascript -e 'tell application "Safari" to do JavaScript "location.reload()" in current tab of front window'
    echo "Reloaded"
    ;;
  back)
    osascript -e 'tell application "Safari" to do JavaScript "history.back()" in current tab of front window'
    echo "Went back"
    ;;
  forward)
    osascript -e 'tell application "Safari" to do JavaScript "history.forward()" in current tab of front window'
    echo "Went forward"
    ;;
  screenshot)
    OUTFILE="${VALUE:-/tmp/safari_screenshot.png}"
    osascript -e 'tell application "Safari" to activate'
    sleep 0.5
    screencapture -w "$OUTFILE"
    echo "Screenshot saved to $OUTFILE"
    ;;
  *)
    echo "Usage: safari_control.sh open|navigate|current-url|current-title|list-tabs|close-tab|close-all-tabs|reload|back|forward|screenshot [value]"
    exit 1
    ;;
esac
