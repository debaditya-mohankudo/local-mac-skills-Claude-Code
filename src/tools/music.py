"""
music.py
--------
MCP tool handlers for Music.app control via AppleScript (osascript), ported
1:1 from local-mac-tool/Sources/LocalMacMCP/MusicTool.swift — that Swift tool
already just shelled out to osascript itself, so this is a direct port of
its exact AppleScript strings and return shapes, not a redesign.
"""
from __future__ import annotations

from local_process import run_osascript, LocalProcessError


def _escape(s: str) -> str:
    return s.replace('"', '\\"')


def handle_play() -> str:
    """Start Music.app playback."""
    run_osascript('tell application "Music" to play')
    return "Playback started."


def handle_pause() -> str:
    """Pause Music.app playback."""
    run_osascript('tell application "Music" to pause')
    return "Playback paused."


def handle_next() -> str:
    """Skip to next track."""
    run_osascript('tell application "Music" to next track')
    return "Skipped to next track."


def handle_previous() -> str:
    """Go to previous track."""
    run_osascript('tell application "Music" to previous track')
    return "Went to previous track."


def handle_volume(volume: int) -> str:
    """Set Music.app volume (0–100)."""
    if not (0 <= volume <= 100):
        raise ValueError("volume must be 0–100")
    run_osascript(f'tell application "Music" to set sound volume to {volume}')
    return f"Volume set to {volume}."


def handle_now_playing() -> dict | str:
    """Get currently playing track info."""
    script = """
        tell application "Music"
            if player state is playing or player state is paused then
                set t to current track
                set n to name of t
                set a to artist of t
                set al to album of t
                set d to duration of t
                set pos to player position
                set vol to sound volume as string
                set ps to player state
                set stateStr to "paused"
                if ps is playing then set stateStr to "playing"
                return n & "|||" & a & "|||" & al & "|||" & ((round d) as string) & "|||" & ((round pos) as string) & "|||" & vol & "|||" & stateStr
            else
                return "stopped|||||||"
            end if
        end tell
        """
    result = run_osascript(script)
    parts = result.split("|||")
    if len(parts) < 7 or parts[0] == "stopped":
        return "Music is stopped."
    name, artist, album = parts[0], parts[1], parts[2]
    duration = int(parts[3]) if parts[3].isdigit() else 0
    position = int(parts[4]) if parts[4].isdigit() else 0
    volume = parts[5]
    state = parts[6].strip()
    d_min, d_sec = divmod(duration, 60)
    p_min, p_sec = divmod(position, 60)
    return {
        "state": state,
        "track": name,
        "artist": artist,
        "album": album,
        "position": f"{p_min}:{p_sec:02d}",
        "duration": f"{d_min}:{d_sec:02d}",
        "volume": volume,
    }


def handle_search_play(query: str) -> str:
    """Search library and play first match."""
    if not query:
        raise ValueError("Missing required argument: query")
    escaped = _escape(query)
    script = f"""
        tell application "Music"
            set results to (search playlist "Library" for "{escaped}")
            if results is {{}} then error "No results found for: {escaped}"
            play item 1 of results
        end tell
        """
    run_osascript(script)
    return f"Playing: {query}"


def handle_list_playlists() -> str:
    """List all Music.app playlists."""
    script = """
        tell application "Music"
            set output to ""
            repeat with p in playlists
                set output to output & (name of p) & "\\n"
            end repeat
            return output
        end tell
        """
    result = run_osascript(script)
    return result if result else "No playlists found."


def handle_play_playlist(name: str) -> str:
    """Play a playlist by exact name."""
    if not name:
        raise ValueError("Missing required argument: name")
    escaped = _escape(name)
    run_osascript(f'tell application "Music" to play playlist "{escaped}"')
    return f"Playing playlist: {name}"


def handle_play_track(playlist: str, index: int) -> str:
    """Play a track by 1-based index in a playlist."""
    if not playlist or index < 1:
        raise ValueError("Missing required arguments: playlist, index (1-based)")
    escaped = _escape(playlist)
    script = f"""
        tell application "Music"
            set pl to playlist "{escaped}"
            set tr to track {index} of pl
            play tr
        end tell
        """
    run_osascript(script)
    return f'Playing track {index} of "{playlist}".'


def handle_list_tracks(playlist: str) -> dict | str:
    """List tracks in a playlist."""
    if not playlist:
        raise ValueError("Missing required argument: playlist")
    escaped = _escape(playlist)
    script = f"""
        tell application "Music"
            set output to ""
            set pl to playlist "{escaped}"
            repeat with t in tracks of pl
                set output to output & (name of t) & "|||" & (artist of t) & "\\n"
            end repeat
            return output
        end tell
        """
    result = run_osascript(script)
    if not result:
        return f"No tracks found in playlist: {playlist}"
    lines = [l for l in result.split("\n") if l]
    tracks = []
    for i, line in enumerate(lines):
        parts = line.split("|||")
        tracks.append({"index": str(i + 1), "title": parts[0], "artist": parts[1] if len(parts) > 1 else ""})
    return {"playlist": playlist, "count": len(tracks), "tracks": tracks}
