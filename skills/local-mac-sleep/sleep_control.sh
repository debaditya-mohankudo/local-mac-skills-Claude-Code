#!/bin/bash
# Usage: sleep_control.sh <now|in <MINUTES>|cancel|status|winddown [MINUTES]>
#
#   now              — sleep immediately
#   in <MINUTES>     — schedule sleep in N minutes (uses `at`)
#   cancel           — cancel any pending scheduled sleep
#   status           — show pending sleep jobs
#   winddown [MIN]   — quit all apps except VSCode, then sleep
#                      MIN defaults to 0 (immediate); pass a number to delay

CMD="$1"

usage() {
  echo "Usage: sleep_control.sh <now|in <MINUTES>|cancel|status|winddown [MINUTES]>"
  echo ""
  echo "  now              — quit all apps (except VSCode), then sleep"
  echo "  in <MINUTES>     — schedule sleep in N minutes"
  echo "  cancel           — cancel pending scheduled sleep"
  echo "  status           — show pending sleep jobs"
  echo "  winddown [MIN]   — quit all apps except VSCode, then sleep"
  echo "                     MIN defaults to 0 (run now); pass a number to delay"
  exit 1
}

[[ -z "$CMD" ]] && usage

# Tag used to identify our at jobs
AT_TAG="mac_sleep_job"

quit_all_apps() {
  echo "Listing running apps..."
  local APP_NAMES
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

  echo "All apps closed. Waiting for cleanup..."
  sleep 5
}

schedule_winddown() {
  local DELAY_MIN="${1:-0}"

  # Write the wind-down script to a temp file
  local SCRIPT
  SCRIPT=$(mktemp /tmp/sleep_winddown_XXXXXX) && mv "$SCRIPT" "${SCRIPT}.sh" && SCRIPT="${SCRIPT}.sh"
  cat > "$SCRIPT" <<'WINDDOWN'
#!/bin/bash
# List then quit all apps except VSCode (Code) and Finder, one by one
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

echo "All apps closed. Waiting for cleanup..."
sleep 5

# Sleep
pmset sleepnow
WINDDOWN
  chmod +x "$SCRIPT"

  if (( DELAY_MIN <= 0 )); then
    echo "Running wind-down now..."
    bash "$SCRIPT"
  else
    echo "bash $SCRIPT" | at now + "${DELAY_MIN}" minutes 2>&1
    echo "Wind-down scheduled in ${DELAY_MIN} minute(s). Run 'sleep_control.sh status' to see the job, 'cancel' to abort."
  fi
}

case "$CMD" in
  now)
    quit_all_apps
    echo "Sleeping now..."
    pmset sleepnow
    ;;

  in)
    MINUTES="$2"
    if ! [[ "$MINUTES" =~ ^[0-9]+$ ]] || (( MINUTES < 1 )); then
      echo "ERROR: MINUTES must be a positive integer. Example: sleep_control.sh in 30"
      exit 1
    fi
    OUTPUT=$(echo "pmset sleepnow" | at now + "${MINUTES}" minutes 2>&1)
    echo "$OUTPUT"
    JOB_ID=$(echo "$OUTPUT" | grep -oE 'job [0-9]+' | awk '{print $2}')
    [[ -n "$JOB_ID" ]] && echo "Sleep scheduled in ${MINUTES} minute(s) (job $JOB_ID). Cancel with: sleep_control.sh cancel"
    ;;

  cancel)
    JOBS=$(atq 2>/dev/null)
    if [[ -z "$JOBS" ]]; then
      echo "No scheduled sleep jobs found."
    else
      echo "Cancelling all scheduled at jobs:"
      echo "$JOBS"
      echo "$JOBS" | awk '{print $1}' | xargs -r atrm
      echo "Cancelled."
    fi
    ;;

  status)
    JOBS=$(atq 2>/dev/null)
    if [[ -z "$JOBS" ]]; then
      echo "No scheduled sleep (or at) jobs."
    else
      echo "Scheduled at jobs:"
      echo "$JOBS"
    fi
    ;;

  winddown)
    DELAY="${2:-0}"
    if ! [[ "$DELAY" =~ ^[0-9]+$ ]]; then
      echo "ERROR: MINUTES must be a non-negative integer. Example: sleep_control.sh winddown 30"
      exit 1
    fi
    schedule_winddown "$DELAY"
    ;;

  *)
    echo "ERROR: Unknown command: $CMD"
    usage
    ;;
esac
