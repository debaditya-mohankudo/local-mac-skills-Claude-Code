#!/bin/bash
# Usage: spotify_play.sh SPOTIFY_URI
# Plays a Spotify URI (track, playlist, or album)
# Get URI from Spotify: right-click item → Share → Copy Spotify URI

URI="$1"

if [[ -z "$URI" ]]; then
  echo "Usage: spotify_play.sh SPOTIFY_URI"
  exit 1
fi

osascript -e "tell application \"Spotify\" to play track \"$URI\""
echo "Playing: $URI"
