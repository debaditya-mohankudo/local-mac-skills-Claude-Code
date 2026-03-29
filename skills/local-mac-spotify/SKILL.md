---
name: local-mac-spotify
description: Control Spotify on macOS — play/pause/skip/volume and play saved playlists by nickname. Use when user asks to play music, pause, skip track, change volume, or play a specific playlist.
user-invocable: true
---

Control Spotify on macOS via AppleScript. No API token needed.

> **Config file:** `~/workspace/claude_for_mac_local/spotify_config.py`
> Add your playlist URIs here. Right-click any playlist in Spotify → Share → Copy Spotify URI.

---

## Step 1 — Read config

```bash
cat ~/workspace/claude_for_mac_local/spotify_config.py
```

Extract `PLAYLISTS` dict — nickname → Spotify URI.

---

## Playback controls

```bash
~/workspace/claude_for_mac_local/tools/spotify_control.sh play
~/workspace/claude_for_mac_local/tools/spotify_control.sh pause
~/workspace/claude_for_mac_local/tools/spotify_control.sh next
~/workspace/claude_for_mac_local/tools/spotify_control.sh previous
~/workspace/claude_for_mac_local/tools/spotify_control.sh volume 70
~/workspace/claude_for_mac_local/tools/spotify_control.sh current
```

## Play a playlist by nickname

Look up the nickname in `PLAYLISTS` (case-insensitive). If found:

```bash
~/workspace/claude_for_mac_local/tools/spotify_play.sh "SPOTIFY_URI"
```

If the nickname is not in `PLAYLISTS` — tell the user to add it to `spotify_config.py` with the URI from Spotify (right-click playlist → Share → Copy Spotify URI). Do not guess.

## Guardrails

- Spotify must be open and logged in. If AppleScript errors, tell the user to open Spotify first.
- Never modify `spotify_config.py` without the user providing the exact URI.
