---
name: local-mac-music
description: Control Music.app playback, volume, playlists, and track search. Use for local music control.
user-invocable: true
---

Control Music.app.

## Tools
`music__play` `music__pause` `music__next` `music__previous` `music__now_playing`
`music__volume` `music__search_play` `music__list_playlists` `music__play_playlist`
`music__play_track` `music__list_tracks`

## Rules
- This is Music.app, not Spotify — use `/local-mac-spotify` for that.
- Check `music__now_playing` before reporting what is playing; do not assume.
