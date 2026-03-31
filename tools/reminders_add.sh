#!/bin/bash
# Usage: reminders_add.sh LIST "NAME" ["DUE_DATE"] ["NOTES"]
# Adds a reminder to the specified list.
# DUE_DATE format: "MM/DD/YYYY HH:MM:SS" (optional)
LIST="$1"
NAME="$2"
DUE="$3"
NOTES="$4"

if [ -n "$DUE" ] && [ -n "$NOTES" ]; then
  osascript -e "tell application \"Reminders\" to make new reminder in list \"$LIST\" with properties {name:\"$NAME\", due date:date \"$DUE\", body:\"$NOTES\"}"
elif [ -n "$DUE" ]; then
  osascript -e "tell application \"Reminders\" to make new reminder in list \"$LIST\" with properties {name:\"$NAME\", due date:date \"$DUE\"}"
elif [ -n "$NOTES" ]; then
  osascript -e "tell application \"Reminders\" to make new reminder in list \"$LIST\" with properties {name:\"$NAME\", body:\"$NOTES\"}"
else
  osascript -e "tell application \"Reminders\" to make new reminder in list \"$LIST\" with properties {name:\"$NAME\"}"
fi
