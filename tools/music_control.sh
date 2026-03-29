#!/bin/bash
# Usage: music_control.sh COMMAND [VALUE]
# Commands: play, pause, next, previous, volume, current, list-playlists
# volume requires VALUE between 0-100

COMMAND="$1"
VALUE="$2"

case "$COMMAND" in
  play)
    osascript -e 'tell application "Music" to play'
    echo "Playing"
    ;;
  pause)
    osascript -e 'tell application "Music" to pause'
    echo "Paused"
    ;;
  next)
    osascript -e 'tell application "Music" to next track'
    echo "Skipped to next track"
    ;;
  previous)
    osascript -e 'tell application "Music" to previous track'
    echo "Went to previous track"
    ;;
  volume)
    if [[ -z "$VALUE" ]]; then
      echo "Usage: music_control.sh volume 0-100"
      exit 1
    fi
    PREV=$(osascript -e 'tell application "Music" to return sound volume')
    osascript -e "tell application \"Music\" to set sound volume to $VALUE"
    echo "Volume changed from $PREV to $VALUE"
    ;;
  current)
    osascript -e '
      tell application "Music"
        set t to name of current track
        set a to artist of current track
        set al to album of current track
        set s to player state as string
        set v to sound volume
        return "Track: " & t & "\nArtist: " & a & "\nAlbum: " & al & "\nState: " & s & "\nVolume: " & v
      end tell'
    ;;
  get-volume)
    osascript -e 'tell application "Music" to return sound volume'
    ;;
  list-playlists)
    osascript -e 'tell application "Music" to get name of every playlist'
    ;;
  *)
    echo "Usage: music_control.sh play|pause|next|previous|current|get-volume|volume [0-100]|list-playlists"
    exit 1
    ;;
esac
