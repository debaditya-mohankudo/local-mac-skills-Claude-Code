#!/bin/bash
# Usage: music_play.sh "PLAYLIST NAME"
# Plays an iMusic playlist by its exact name in your library.

PLAYLIST="$1"

if [[ -z "$PLAYLIST" ]]; then
  echo "Usage: music_play.sh \"PLAYLIST NAME\""
  exit 1
fi

osascript -e "tell application \"Music\" to play playlist \"$PLAYLIST\""
echo "Playing playlist: $PLAYLIST"
