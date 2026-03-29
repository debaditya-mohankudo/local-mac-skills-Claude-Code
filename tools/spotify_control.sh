#!/bin/bash
# Usage: spotify_control.sh COMMAND [VALUE]
# Commands: play, pause, next, previous, volume, current
# volume requires a VALUE between 0-100

COMMAND="$1"
VALUE="$2"

case "$COMMAND" in
  play)
    osascript -e 'tell application "Spotify" to play'
    echo "Playing"
    ;;
  pause)
    osascript -e 'tell application "Spotify" to pause'
    echo "Paused"
    ;;
  next)
    osascript -e 'tell application "Spotify" to next track'
    echo "Skipped to next track"
    ;;
  previous)
    osascript -e 'tell application "Spotify" to previous track'
    echo "Went to previous track"
    ;;
  volume)
    if [[ -z "$VALUE" ]]; then
      echo "Usage: spotify_control.sh volume 0-100"
      exit 1
    fi
    osascript -e "tell application \"Spotify\" to set sound volume to $VALUE"
    echo "Volume set to $VALUE"
    ;;
  current)
    osascript -e '
      tell application "Spotify"
        set t to name of current track
        set a to artist of current track
        set al to album of current track
        set s to player state as string
        return "Track: " & t & "\nArtist: " & a & "\nAlbum: " & al & "\nState: " & s
      end tell'
    ;;
  *)
    echo "Usage: spotify_control.sh play|pause|next|previous|current|volume [0-100]"
    exit 1
    ;;
esac
