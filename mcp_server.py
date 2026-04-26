"""Single MCP server — local-mac tools (via Swift CLI) + vault (filesystem)."""
import os
import subprocess
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from mcp.server.fastmcp import FastMCP
from swift_bridge import call_swift # type: ignore

VAULT_NAME = os.environ.get("VAULT_NAME", "claude_documents")
VAULT_PATH = Path(os.environ.get("VAULT_PATH", Path.home() / "workspace" / "claude_documents"))
mcp = FastMCP("local-mac")

# ---------------------------------------------------------------------------
# Mail
# ---------------------------------------------------------------------------

@mcp.tool()
def mail_read(limit: int = 20, folder: str = "INBOX") -> dict:
    """Read recent emails from a mailbox folder."""
    return call_swift("mail-read", {"limit": limit, "folder": folder})


@mcp.tool()
def mail_search(query: str, folder: str = "", limit: int = 50) -> dict:
    """Search emails by subject, sender, or preview text. Searches all folders if folder is empty."""
    return call_swift("mail-search", {"query": query, "folder": folder, "limit": limit})


@mcp.tool()
def mail_list_mailboxes() -> dict:
    """List all Mail.app mailboxes."""
    return call_swift("mail-list-mailboxes")


@mcp.tool()
def mail_compose(to: str, subject: str = "", body: str = "") -> dict:
    """Open a pre-filled compose window in Mail.app. Does not send — user reviews and sends manually."""
    return call_swift("mail-compose", {"to": to, "subject": subject, "body": body})


# ---------------------------------------------------------------------------
# iMessage
# ---------------------------------------------------------------------------

@mcp.tool()
def imessage_send(recipient: str, message: str, delay_seconds: int = 0) -> str:
    """Send an iMessage to a recipient (phone number or email)."""
    return call_swift("imessage-send", {"recipient": recipient, "message": message, "delay_seconds": delay_seconds})


@mcp.tool()
def imessage_read(limit: int = 10, direction: str = "received") -> dict:
    """Read recent iMessages. direction: received | sent | all"""
    return call_swift("imessage-read", {"limit": limit, "direction": direction})


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------

@mcp.tool()
def contacts_search(name: str, include_email: bool = False) -> dict:
    """Search contacts by name (vault-first, CNContactStore fallback)."""
    return call_swift("contacts-search", {"name": name, "include_email": include_email})


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

@mcp.tool()
def calendar_list_events(start_date: str, end_date: str) -> dict:
    """List calendar events between ISO-8601 start and end dates (YYYY-MM-DD or full ISO-8601)."""
    def _iso(d: str) -> str:
        return d if "T" in d else f"{d}T00:00:00Z"
    return call_swift("calendar-list-events", {"start_date": _iso(start_date), "end_date": _iso(end_date)})


@mcp.tool()
def calendar_add_event(title: str, start_date: str, calendar: str = "Work",
                       end_date: str = None, notes: str = None) -> str:
    """Add a calendar event."""
    payload = {"title": title, "start_date": start_date, "calendar": calendar}
    if end_date: payload["end_date"] = end_date
    if notes: payload["notes"] = notes
    return call_swift("calendar-add-event", payload)


@mcp.tool()
def calendar_delete_event(title: str, calendar: str = "Work") -> str:
    """Delete a calendar event by title (must be unique match within ±30 days)."""
    return call_swift("calendar-delete-event", {"title": title, "calendar": calendar})


@mcp.tool()
def calendar_get_events_by_date(date: str) -> dict:
    """Get market calendar events from SQLite for a specific date (YYYY-MM-DD)."""
    return call_swift("calendar-get-events-by-date", {"date": date})


@mcp.tool()
def calendar_get_upcoming_events(days_ahead: int = 7, from_date: str = "") -> dict:
    """Get upcoming market calendar events from SQLite."""
    return call_swift("calendar-get-upcoming-events", {"days_ahead": days_ahead, "from_date": from_date})


@mcp.tool()
def calendar_get_noise_summary(date: str) -> dict:
    """Get per-asset noise summary for a date from SQLite calendar."""
    return call_swift("calendar-get-noise-summary", {"date": date})


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------

@mcp.tool()
def reminders_list(list: str = None, include_completed: bool = False) -> dict:
    """List reminders. Optionally filter by list name."""
    payload = {"include_completed": include_completed}
    if list: payload["list"] = list
    return call_swift("reminders-list", payload)


@mcp.tool()
def reminders_create(title: str, list: str = None, due_date: str = None, notes: str = None) -> str:
    """Create a reminder."""
    payload = {"title": title}
    if list: payload["list"] = list
    if due_date: payload["due_date"] = due_date
    if notes: payload["notes"] = notes
    return call_swift("reminders-create", payload)


@mcp.tool()
def reminders_complete(id: str) -> str:
    """Mark a reminder complete by its identifier."""
    return call_swift("reminders-complete", {"id": id})


@mcp.tool()
def reminders_delete(id: str) -> str:
    """Delete a reminder by its identifier."""
    return call_swift("reminders-delete", {"id": id})


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------

@mcp.tool()
def notes_list(folder: str = "", limit: int = 20) -> dict:
    """List Apple Notes."""
    return call_swift("notes-list", {"folder": folder, "limit": limit})


@mcp.tool()
def notes_read(id: str) -> dict:
    """Read an Apple Note by identifier."""
    return call_swift("notes-read", {"id": id})


@mcp.tool()
def notes_folders() -> dict:
    """List Apple Notes folders."""
    return call_swift("notes-folders")


@mcp.tool()
def notes_add(title: str, body: str = "", folder: str = "Notes") -> str:
    """Create a new Apple Note."""
    return call_swift("notes-add", {"title": title, "body": body, "folder": folder})


@mcp.tool()
def notes_delete(title: str, folder: str = "Notes") -> str:
    """Delete an Apple Note by title from a folder."""
    return call_swift("notes-delete", {"title": title, "folder": folder})


# ---------------------------------------------------------------------------
# Music
# ---------------------------------------------------------------------------

@mcp.tool()
def music_play() -> str:
    """Start Music.app playback."""
    return call_swift("music-play")


@mcp.tool()
def music_pause() -> str:
    """Pause Music.app playback."""
    return call_swift("music-pause")


@mcp.tool()
def music_next() -> str:
    """Skip to next track."""
    return call_swift("music-next")


@mcp.tool()
def music_previous() -> str:
    """Go to previous track."""
    return call_swift("music-previous")


@mcp.tool()
def music_now_playing() -> dict:
    """Get currently playing track info."""
    return call_swift("music-now-playing")


@mcp.tool()
def music_volume(volume: int) -> str:
    """Set Music.app volume (0–100)."""
    return call_swift("music-volume", {"volume": volume})


@mcp.tool()
def music_search_play(query: str) -> str:
    """Search library and play first match."""
    return call_swift("music-search-play", {"query": query})


@mcp.tool()
def music_list_playlists() -> str:
    """List all Music.app playlists."""
    return call_swift("music-list-playlists")


@mcp.tool()
def music_play_playlist(name: str) -> str:
    """Play a playlist by exact name."""
    return call_swift("music-play-playlist", {"name": name})


@mcp.tool()
def music_play_track(playlist: str, index: int) -> str:
    """Play a track by 1-based index in a playlist."""
    return call_swift("music-play-track", {"playlist": playlist, "index": index})


@mcp.tool()
def music_list_tracks(playlist: str) -> dict:
    """List tracks in a playlist."""
    return call_swift("music-list-tracks", {"playlist": playlist})


# ---------------------------------------------------------------------------
# Safari
# ---------------------------------------------------------------------------

@mcp.tool()
def safari_open(url: str) -> str:
    """Open a URL in Safari (allowlist enforced)."""
    return call_swift("safari-open", {"url": url})


@mcp.tool()
def safari_navigate(url: str) -> str:
    """Navigate the current Safari tab to a URL (allowlist enforced)."""
    return call_swift("safari-navigate", {"url": url})


@mcp.tool()
def safari_current_url() -> str:
    """Get the URL of Safari's current tab."""
    return call_swift("safari-current-url")


@mcp.tool()
def safari_current_title() -> str:
    """Get the title of Safari's current tab."""
    return call_swift("safari-current-title")


@mcp.tool()
def safari_list_tabs() -> str:
    """List all open Safari tabs."""
    return call_swift("safari-list-tabs")


@mcp.tool()
def safari_close_tab() -> str:
    """Close Safari's current tab."""
    return call_swift("safari-close-tab")


@mcp.tool()
def safari_close_all_tabs() -> str:
    """Close all Safari tabs."""
    return call_swift("safari-close-all-tabs")


@mcp.tool()
def safari_reload() -> str:
    """Reload Safari's current tab."""
    return call_swift("safari-reload")


@mcp.tool()
def safari_back() -> str:
    """Navigate back in Safari."""
    return call_swift("safari-back")


@mcp.tool()
def safari_forward() -> str:
    """Navigate forward in Safari."""
    return call_swift("safari-forward")


@mcp.tool()
def safari_screenshot(outfile: str = None) -> str:
    """Take a screenshot of Safari's current tab."""
    payload = {}
    if outfile: payload["outfile"] = outfile
    return call_swift("safari-screenshot", payload)


@mcp.tool()
def safari_js(js: str) -> str:
    """Execute JavaScript in Safari's current tab."""
    return call_swift("safari-js", {"js": js})


@mcp.tool()
def safari_read(mode: str) -> str:
    """Read page content from Safari. mode: text|html|links|title|selected"""
    return call_swift("safari-read", {"mode": mode})


# ---------------------------------------------------------------------------
# Sleep / Notify / Clipboard / Process / Finder / iCloud
# ---------------------------------------------------------------------------

@mcp.tool()
def sleep_now() -> str:
    """Put Mac to sleep immediately."""
    return call_swift("sleep-now")


@mcp.tool()
def sleep_in(minutes: int) -> str:
    """Schedule sleep after N minutes."""
    return call_swift("sleep-in", {"minutes": minutes})


@mcp.tool()
def sleep_cancel() -> str:
    """Cancel scheduled sleep."""
    return call_swift("sleep-cancel")


@mcp.tool()
def sleep_status() -> str:
    """Check scheduled sleep status."""
    return call_swift("sleep-status")


@mcp.tool()
def sleep_winddown(minutes: int = 30) -> str:
    """Start wind-down routine before sleep."""
    return call_swift("sleep-winddown", {"minutes": minutes})


@mcp.tool()
def notify_send(title: str, body: str = "", subtitle: str = "") -> str:
    """Send a macOS notification."""
    return call_swift("notify-send", {"title": title, "body": body, "subtitle": subtitle})


@mcp.tool()
def clipboard_read() -> str:
    """Read the macOS clipboard."""
    return call_swift("clipboard-read")


@mcp.tool()
def clipboard_write(text: str) -> str:
    """Write text to the macOS clipboard."""
    return call_swift("clipboard-write", {"text": text})


@mcp.tool()
def process_list(name: str = "") -> dict: # type: ignore
    """List running processes, optionally filtered by name."""
    payload = {}
    if name: payload["name"] = name
    return call_swift("process-list", payload)


@mcp.tool()
def process_kill(pid: int) -> str:
    """Kill a process by PID."""
    return call_swift("process-kill", {"pid": pid})


@mcp.tool()
def spotlight_search(query: str, path: str = "") -> dict: # type: ignore
    """Search files with Spotlight (mdfind)."""
    payload = {"query": query}
    if path: payload["path"] = path
    return call_swift("spotlight-search", payload)


@mcp.tool()
def icloud_list(path: str = "") -> dict:
    """List iCloud Drive contents at a given subpath."""
    return call_swift("icloud-list", {"path": path})


@mcp.tool()
def foundation_models_query(prompt: str, system: str = None, max_tokens: int = 256) -> str:
    """Query Apple Foundation Models (on-device LLM, macOS 26+) with a prompt."""
    payload = {"prompt": prompt, "max_tokens": max_tokens}
    if system: payload["system"] = system
    return call_swift("foundation-models-query", payload)


# ---------------------------------------------------------------------------
# Podcasts
# ---------------------------------------------------------------------------

@mcp.tool()
def podcasts_list() -> list:
    """List all subscribed podcasts with episode counts."""
    return call_swift("podcasts-list")

@mcp.tool()
def podcasts_episodes(podcast_title: str = "", podcast_uuid: str = "", limit: int = 20, unplayed: bool = False) -> list:
    """List episodes for a podcast. Provide podcast_title (partial match) or podcast_uuid."""
    payload: dict = {"limit": limit, "unplayed": unplayed}
    if podcast_uuid: payload["podcast_uuid"] = podcast_uuid
    elif podcast_title: payload["podcast_title"] = podcast_title
    else: raise ValueError("Provide podcast_title or podcast_uuid")
    return call_swift("podcasts-episodes", payload)

@mcp.tool()
def podcasts_recent(limit: int = 20, new_only: bool = False) -> list:
    """List recent episodes across all podcasts. Set new_only=True for unheard episodes."""
    return call_swift("podcasts-recent", {"limit": limit, "new_only": new_only})

@mcp.tool()
def podcasts_in_progress() -> list:
    """List episodes that have been started but not finished (have a playhead position)."""
    return call_swift("podcasts-in-progress")


# ---------------------------------------------------------------------------
# Surfshark VPN
# ---------------------------------------------------------------------------

@mcp.tool()
def surfshark_status() -> dict:
    """Get Surfshark VPN connection status — connected/disconnected, server location, protocol, DNS, and post-quantum status."""
    return call_swift("surfshark-status")


# ---------------------------------------------------------------------------
# Obsidian vault — dispatcher
# ---------------------------------------------------------------------------

import re as _re

def _vault_path(path: str) -> Path:
    """Resolve a vault-relative path to an absolute Path, ensuring .md extension."""
    p = path if path.endswith(".md") else path + ".md"
    return VAULT_PATH / p


def _dispatch_obsidian(op: str, path: str = "", content: str = "", to: str = "",
                       query: str = "", project_folder: str = "", max_results: int = 5,
                       scope: str = "all") -> str:
    match op:
        case "read":
            fp = _vault_path(path)
            if not fp.exists():
                raise FileNotFoundError(f"Note not found: {path}")
            return fp.read_text()

        case "create":
            fp = _vault_path(path)
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content)
            return f"✓ Written: {path}"

        case "append":
            fp = _vault_path(path)
            if not fp.exists():
                raise FileNotFoundError(f"Note not found: {path}")
            fp.write_text(fp.read_text() + "\n" + content)
            return f"✓ Appended to: {path}"

        case "delete":
            fp = _vault_path(path)
            if not fp.exists():
                raise FileNotFoundError(f"Note not found: {path}")
            fp.unlink()
            return f"✓ Deleted: {path}"

        case "move":
            src = _vault_path(path)
            dst = _vault_path(to)
            if not src.exists():
                raise FileNotFoundError(f"Note not found: {path}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            return f"✓ Moved: {path} → {to}"

        case "files":
            base = VAULT_PATH / path if path else VAULT_PATH
            files = sorted(str(f.relative_to(VAULT_PATH)) for f in VAULT_PATH.rglob("*.md")
                           if not any(p.startswith(".") for p in f.parts))
            return "\n".join(f for f in files if not path or f.startswith(path))

        case "search":
            results, seen = [], {}
            query_lower = query.lower()
            search_root = VAULT_PATH / project_folder if project_folder else VAULT_PATH
            for fp in search_root.rglob("*.md"):
                if any(p.startswith(".") for p in fp.parts):
                    continue
                text = fp.read_text(errors="ignore")
                if query_lower in text.lower():
                    rel = str(fp.relative_to(VAULT_PATH))
                    if rel not in seen:
                        seen[rel] = True
                        idx = text.lower().find(query_lower)
                        snippet = text[max(0, idx-50):idx+150].replace("\n", " ").strip()
                        results.append(f"**{rel}**: {snippet}")
                        if len(results) >= max_results:
                            break
            return "\n".join(results) if results else f"No results for: {query}"

        case "links":
            fp = _vault_path(path)
            text = fp.read_text(errors="ignore")
            links = _re.findall(r"\[\[([^\]|#]+)", text)
            return "\n".join(sorted(set(links))) if links else "No outgoing links."

        case "backlinks":
            target = Path(path).stem.lower()
            matches = []
            for fp in VAULT_PATH.rglob("*.md"):
                if any(p.startswith(".") for p in fp.parts):
                    continue
                if target in fp.read_text(errors="ignore").lower():
                    matches.append(str(fp.relative_to(VAULT_PATH)))
            return "\n".join(sorted(matches)) if matches else "No backlinks found."

        case "daily":
            today = date.today().strftime("%Y-%m-%d")
            fp = VAULT_PATH / "Daily" / f"{today}_summary.md"
            return fp.read_text() if fp.exists() else f"No daily summary for {today}."

        case "outline":
            fp = _vault_path(path)
            headings = [l.rstrip() for l in fp.read_text(errors="ignore").splitlines()
                        if l.startswith("#")]
            return "\n".join(headings) if headings else "No headings found."

        case "tags":
            tag_pattern = _re.compile(r"(?:^tags:\s*\[([^\]]+)\]|#([\w/]+))", _re.MULTILINE)
            counts: dict[str, int] = {}
            files_to_scan = [_vault_path(path)] if path else list(VAULT_PATH.rglob("*.md"))
            for fp in files_to_scan:
                if not fp.exists():
                    continue
                text = fp.read_text(errors="ignore")
                for m in tag_pattern.finditer(text):
                    for tag in (m.group(1) or "").split(",") + ([m.group(2)] if m.group(2) else []):
                        tag = tag.strip()
                        if tag:
                            counts[tag] = counts.get(tag, 0) + 1
            return "\n".join(f"{t}: {c}" for t, c in sorted(counts.items(), key=lambda x: -x[1]))

        case "tasks":
            task_re = _re.compile(r"- \[ \] (.+)")
            results = []
            if scope == "daily":
                today = date.today().strftime("%Y-%m-%d")
                files = [VAULT_PATH / "Daily" / f"{today}_summary.md"]
            elif scope == "all":
                files = [f for f in VAULT_PATH.rglob("*.md") if not any(p.startswith(".") for p in f.parts)]
            else:
                files = [_vault_path(scope)]
            for fp in files:
                if not fp.exists():
                    continue
                for m in task_re.finditer(fp.read_text(errors="ignore")):
                    results.append(f"[{fp.relative_to(VAULT_PATH)}] {m.group(1)}")
            return "\n".join(results) if results else "No incomplete tasks found."

        case "stats":
            all_files = [f for f in VAULT_PATH.rglob("*.md") if not any(p.startswith(".") for p in f.parts)]
            return f"Vault: {VAULT_NAME}\nTotal notes: {len(all_files)}"

        case _:
            raise ValueError(f"Unknown obsidian op: {op!r}. Valid: read, create, append, delete, move, files, search, links, backlinks, daily, outline, tags, tasks, stats")


@mcp.tool()
def vault_read(path: str) -> str:
    """Read a note from the vault."""
    return _dispatch_obsidian("read", path=path)

@mcp.tool()
def vault_write(path: str, content: str) -> str:
    """Create or overwrite a vault note."""
    return _dispatch_obsidian("create", path=path, content=content)

@mcp.tool()
def vault_append(path: str, content: str) -> str:
    """Append content to an existing vault note."""
    return _dispatch_obsidian("append", path=path, content=content)

@mcp.tool()
def vault_delete(path: str) -> str:
    """Delete a vault note."""
    return _dispatch_obsidian("delete", path=path)

@mcp.tool()
def vault_move(path: str, to: str) -> str:
    """Move or rename a vault note."""
    return _dispatch_obsidian("move", path=path, to=to)

@mcp.tool()
def vault_list(path: str = "") -> str:
    """List .md files in the vault or a specific folder."""
    return _dispatch_obsidian("files", path=path)

@mcp.tool()
def vault_search(query: str, project_folder: str = "", max_results: int = 5) -> str:
    """Full-text search the vault with context snippets."""
    return _dispatch_obsidian("search", query=query, project_folder=project_folder, max_results=max_results)

@mcp.tool()
def vault_links(path: str) -> str:
    """List all outgoing [[wikilinks]] from a vault note."""
    return _dispatch_obsidian("links", path=path)

@mcp.tool()
def vault_backlinks(path: str) -> str:
    """Find all notes that link to a given vault note."""
    return _dispatch_obsidian("backlinks", path=path)

@mcp.tool()
def vault_daily_read() -> str:
    """Read today's daily summary note (Daily/YYYY-MM-DD_summary.md)."""
    return _dispatch_obsidian("daily")

@mcp.tool()
def vault_outline(path: str) -> str:
    """Show the heading tree for a vault note."""
    return _dispatch_obsidian("outline", path=path)

@mcp.tool()
def vault_tags(path: str = "") -> str:
    """List tags in the vault or for a specific note."""
    return _dispatch_obsidian("tags", path=path)

@mcp.tool()
def vault_tasks(scope: str = "all") -> str:
    """List incomplete tasks. scope: 'all', 'daily', or a note path."""
    return _dispatch_obsidian("tasks", scope=scope)

@mcp.tool()
def vault_stats() -> str:
    """Get total note count for the vault."""
    return _dispatch_obsidian("stats")


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------

@mcp.tool()
def time_now() -> str:
    """Get the current time in IST."""
    return call_swift("time-now")


@mcp.tool()
def time_alarm(time: str, label: str = "Alarm", reminder: bool = False) -> str:
    """Set an alarm at HH:MM (24h). Optionally also creates an Apple Reminder."""
    return call_swift("time-alarm", {"time": time, "label": label, "reminder": reminder})


@mcp.tool()
def time_wait(minutes: float, label: str = "Timer") -> str:
    """Start a countdown timer for N minutes. Fires a macOS notification when done."""
    return call_swift("time-wait", {"minutes": minutes, "label": label})


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
