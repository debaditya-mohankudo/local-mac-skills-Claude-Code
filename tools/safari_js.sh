#!/bin/bash
# Usage: safari_js.sh "JAVASCRIPT CODE"
# Executes JavaScript in the current Safari tab and returns the result.
# Requires: Safari → Develop menu → Allow JavaScript from Apple Events

JS="$1"

if [[ -z "$JS" ]]; then
  echo "Usage: safari_js.sh \"JS CODE\""
  exit 1
fi

osascript -e "tell application \"Safari\" to do JavaScript \"$JS\" in current tab of front window"
