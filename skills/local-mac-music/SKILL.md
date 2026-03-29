---
name: local-mac-music
description: Control iMusic on macOS — play/pause/skip/volume and play saved playlists by nickname. Use when user asks to play iMusic, play a playlist, pause, skip track, or change volume.
user-invocable: true
---

Control iMusic on macOS via AppleScript. No API token needed.

> **Config file:** `~/workspace/claude_for_mac_local/music_config.py`
> Map short nicknames to exact playlist names in your iMusic library.

---

## Step 1 — Read config

```bash
cat ~/workspace/claude_for_mac_local/music_config.py
```

Extract `PLAYLISTS` dict — nickname → exact iMusic playlist name.

---

## Playback controls

| User says | Command |
|-----------|---------|
| play / resume | `music_control.sh play` |
| pause / stop | `music_control.sh pause` |
| next / skip | `music_control.sh next` |
| previous / back | `music_control.sh previous` |
| set volume to N | `music_control.sh volume N` (0–100) |
| what's the volume / current volume | `music_control.sh get-volume` |
| what's playing / current track | `music_control.sh current` |

```bash
~/workspace/claude_for_mac_local/tools/music_control.sh play
~/workspace/claude_for_mac_local/tools/music_control.sh pause
~/workspace/claude_for_mac_local/tools/music_control.sh next
~/workspace/claude_for_mac_local/tools/music_control.sh previous
~/workspace/claude_for_mac_local/tools/music_control.sh volume 70
~/workspace/claude_for_mac_local/tools/music_control.sh get-volume
~/workspace/claude_for_mac_local/tools/music_control.sh current
```

## List all playlists

When the user asks to list playlists or runs `/local-mac-music list-playlists`:

```bash
~/workspace/claude_for_mac_local/tools/music_control.sh list-playlists
```

Display the results in a readable grouped format (Smart/Default, Your Playlists, Artist Essentials, etc.).

## Play a playlist by nickname

Look up the nickname in `PLAYLISTS` (case-insensitive). If found, use the mapped playlist name:

```bash
~/workspace/claude_for_mac_local/tools/music_play.sh "EXACT PLAYLIST NAME"
```

If the nickname is not in `PLAYLISTS` — tell the user to add it to `music_config.py`. The playlist name must match exactly as it appears in Music.app. Do not guess.

## Guardrails

- Music.app must be open. If AppleScript errors, tell the user to open Music first.
- Playlist names are case-sensitive — use the exact name from the config.
- Never modify `music_config.py` without the user confirming the exact playlist name.
