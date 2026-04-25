---
name: local-mac-music
description: Control iMusic on macOS — play/pause/skip/volume and play saved playlists by nickname. Use when user asks to play iMusic, play a playlist, pause, skip track, or change volume.
user-invocable: true
---

Control iMusic on macOS via MCP tools. No API token needed.

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

| User says | MCP tool |
|-----------|---------|
| play / resume | `mcp__local-mac__music_play` |
| pause / stop | `mcp__local-mac__music_pause` |
| next / skip | `mcp__local-mac__music_next` |
| previous / back | `mcp__local-mac__music_previous` |
| set volume to N | `mcp__local-mac__music_volume` (0–100) |
| what's playing / current track | `mcp__local-mac__music_now_playing` |

## List all playlists

When the user asks to list playlists or runs `/local-mac-music list-playlists`:

Use `mcp__local-mac__music_list_playlists`.

Display the results in a readable grouped format (Smart/Default, Your Playlists, Artist Essentials, etc.).

## Play a playlist by nickname

Look up the nickname in `PLAYLISTS` (case-insensitive). If found, use the mapped playlist name:

Use `mcp__local-mac__music_play_playlist` with the exact playlist name.

If the nickname is not in `PLAYLISTS` — tell the user to add it to `music_config.py`. The playlist name must match exactly as it appears in Music.app. Do not guess.

## Guardrails

- Music.app must be open. If AppleScript errors, tell the user to open Music first.
- Playlist names are case-sensitive — use the exact name from the config.
- Never modify `music_config.py` without the user confirming the exact playlist name.
