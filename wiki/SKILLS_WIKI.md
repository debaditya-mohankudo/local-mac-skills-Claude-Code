# Claude Skills Wiki

Slash commands and skills for local macOS operations.

**Last updated:** 2026-03-22

---

## Two types of skills

Skills in this project fall into two distinct categories:

### Type 1 — Capability skills

These do things Claude Code **cannot do on its own**. They use AppleScript (`osascript`) or system APIs that the Bash tool has no direct access to.

| Skill | Why it needs a skill |
| ----- | -------------------- |
| `local-mac-imessage` | Sends via Messages.app AppleScript — no CLI equivalent |
| `local-mac-mail` | Reads via Mail.app AppleScript — IMAP not configured |
| `local-mac-calendar` | Reads/writes via Calendar.app AppleScript |
| `local-mac-notes` | Reads/writes via Notes.app AppleScript |
| `local-mac-reminders` | Reads/writes via Reminders.app AppleScript |
| `local-mac-contacts` | Searches via Contacts.app AppleScript |
| `local-mac-music` | Controls Music.app via AppleScript |
| `local-mac-spotify` | Controls Spotify via AppleScript |
| `local-mac-safari` | Controls Safari tabs + JS execution via AppleScript |
| `local-mac-finder` | Controls Finder via AppleScript |

### Type 2 — Discipline skills

These wrap commands Claude Code **could already run** via the Bash tool (`docker`, `git`, `lsof`, `curl`, `ps`, etc.). The skill adds no new capability — it adds **guardrails, consistency, and safe defaults** that the Bash tool alone cannot enforce.

| Skill | What the skill enforces that Bash alone cannot |
| ----- | ---------------------------------------------- |
| `local-mac-network` | Port range validation, ping cap, DNS type allowlist, response truncation |
| `local-mac-process` | PID < 100 guard, critical process name block, y/N before kill |
| `local-mac-docker` | Compose action allowlist, no `--follow`/`--no-stream` discipline, confirmation on destructive ops |
| `local-mac-storage` | Safe-only cleanup recommendations, never suggests deleting app data or system dirs |
| `local-mac-screencapture` | One active recording at a time, SIGINT for clean file finalization, no audio |
| `local-mac-ssh` | ControlMaster reuse, BatchMode, destructive command confirmation, config-driven hosts |
| `local-mac-sync-iphone` | Confirmation workflow for remote commands, state tracking for pending approvals, 5-min timeout, activity logging |

**The real value of Type 2 skills is guardrails, not commands.** Without them, Claude makes ad-hoc judgment calls each time. With them, safety is enforced at the script level regardless of what Claude decides in the moment.

---

## macOS Local Skills

These skills interact with native macOS apps via AppleScript (`osascript`). Available globally and in any project.

### `/local-mac-imessage`

Send iMessages on macOS.

- Send a message to a phone number or Apple ID email
- Supports multiple recipients (one call per recipient)
- Invoke: `/local-mac-imessage` or say "send an iMessage to X"
- File: `~/.claude/skills/local-mac-imessage/SKILL.md`

#### Usage — /local-mac-imessage

```text
send "Hello from Claude" to +91XXXXXXXXXX
send "Good morning" to user@example.com
```

#### Check recent iMessages

- Read iMessages from the last N minutes (default: 30)
- Filter by specific contact phone number
- **Privacy-first**: Use `--preview` flag to redact message content and confirm before reading
- Requires **Full Disk Access** for the terminal app in System Settings → Privacy & Security → Full Disk Access
- If not granted, `sqlite3` will fail with `authorization denied` on `chat.db`

**Preview with redaction:**

```bash
imessage_check.sh --preview 60          # Show redacted preview, ask before showing content
imessage_check.sh --preview 120 +91XXXXXXXXXX  # Redacted preview for specific contact
```

**Default behavior (show all):**

```bash
imessage_check.sh 60                    # Show all messages directly
imessage_check.sh 60 +91XXXXXXXXXX      # Filter by contact
```

**Configuration:**

- Set default phone number in `.env` file: `IMESSAGE_PHONE_NUMBER=+91XXXXXXXXXX`
- Messages include text and media attachments
- Full Disk Access required to read message database

---

### `/local-mac-mail`

Read emails from macOS Mail app.

- Fetch recent emails from any account by email address or account name
- Defaults to last 5 emails if count not specified
- Shows sender, subject, date, and unread status
- Supports reading full email content by number
- File: `~/.claude/skills/local-mac-mail/SKILL.md`

#### Zoho Mail support ⏳ PENDING

- Zoho IMAP requires a paid plan — add to Apple Mail once subscribed
- Alternative: Zoho Mail API (OAuth) for free access

#### Usage — /local-mac-mail

```text
/local-mac-mail user@gmail.com 10
check last 5 emails from iCloud
read email 3
```

---

### `/local-mac-calendar`

Read, add, or delete Apple Calendar events.

- Default calendar: **Work** (iCloud)
- Supports: listing events, adding with title/time/notes, deleting by name
- Date range defaults: today, tomorrow, this week (7 days), this month (30 days)
- Skips system calendars: Birthdays, Siri Suggestions, Vedic Astro Events
- File: `~/.claude/skills/local-mac-calendar/SKILL.md`

#### Usage — /local-mac-calendar

```text
show my calendar for this week
add event "Team standup" on Monday at 10am
delete event "Doctor appointment"
```

---

### `/local-mac-notes`

Read, add, or delete Apple Notes.

- Restricted to the **"Claude"** folder only
- Supports: listing all notes, searching by keyword, showing full note, adding, deleting
- Body preview: first 120 chars in list view; full body on `show`
- File: `~/.claude/skills/local-mac-notes/SKILL.md`

#### Usage — /local-mac-notes

```text
list my notes
show note "Meeting summary"
add note "Grocery list" — milk, eggs, bread
delete note "Old draft"
```

---

### `/local-mac-reminders`

Read, add, or delete Apple Reminders.

- Supports all lists, with optional list-name filter
- Status filters: `pending`, `completed`, `all` (default: all)
- Due dates accepted in natural language
- File: `~/workspace/claude_for_mac_local/.claude/skills/local-mac-reminders/SKILL.md`

#### Usage — /local-mac-reminders

```text
show my pending reminders
add reminder "Call dentist" due Friday at 10am
show reminders from Home list
delete reminder "Buy groceries"
```

---

### `/local-mac-music`

Control iMusic on macOS — no API token, no URI. Pure AppleScript.

- Play/pause, skip tracks, go to previous, set volume
- Show current track info
- Play saved playlists by nickname — maps to exact playlist name in Music.app
- Simpler than Spotify: playlist names work directly, no URI needed
- Invoke: `/local-mac-music` or say "play focus playlist", "pause music"
- File: `~/.claude/skills/local-mac-music/SKILL.md`

#### Setup

Add your playlists to `music_config.sh` at the repo root:

- Nickname → exact playlist name as it appears in Music.app (case-sensitive)

#### Usage — /local-mac-music

```text
play focus playlist
pause music
next track
previous track
what's playing?
set volume to 70
what's the volume?
list playlists
/local-mac-music list-playlists
```

| Command | What it does |
| ------- | ------------ |
| `play music` | Resume playback |
| `pause music` | Pause playback |
| `next track` / `skip` | Skip to next track |
| `previous track` / `back` | Go to previous track |
| `set volume to N` | Set volume (0–100); reports previous volume |
| `what's the volume` | Show current volume level |
| `what's playing` | Show track, artist, album, state, and volume |
| `list playlists` | List all playlists from Music.app |

---

### `/local-mac-spotify`

Control Spotify on macOS — no API token, no OAuth. Pure AppleScript.

- Play/pause, skip tracks, go to previous, set volume
- Show current track info
- Play saved playlists by nickname (configured once in `spotify_config.py`)
- Invoke: `/local-mac-spotify` or say "play focus playlist", "pause music"
- File: `~/.claude/skills/local-mac-spotify/SKILL.md`

#### Spotify Setup

Add your playlists to `spotify_config.sh`:

- In Spotify: right-click any playlist → Share → Copy Spotify URI
- Paste the URI as a named entry in `PLAYLISTS`

#### Usage — /local-mac-spotify

```text
play focus playlist
pause spotify
next track
previous track
what's playing?
set volume to 70
```

---

### `/local-mac-finder`

Control macOS Finder — open, reveal, list windows, create folders, move to Trash.

- Get the path of the front Finder window
- List all open Finder windows and their paths
- Get currently selected files/folders
- Open a folder or file in Finder
- Reveal an item (select it in its parent folder)
- Create a new folder and reveal it (restricted to `$HOME`)
- Move a file or folder to Trash (y/N confirmation required)
- Invoke: `/local-mac-finder` or say "open this folder in Finder", "reveal this file", "show selected files"
- File: `~/.claude/skills/local-mac-finder/SKILL.md`

#### Usage — /local-mac-finder

```text
open my workspace folder in Finder
reveal ~/workspace/claude_for_mac_local/tools/finder_read.sh
what's in the current Finder window?
list all open Finder windows
what files do I have selected in Finder?
create a new folder at ~/Desktop/my-project
move ~/Desktop/old-file.txt to Trash
```

---

### `/local-mac-safari`

Control Safari on macOS — navigate, read page content, run JavaScript, interact with elements. Playwright replacement using AppleScript + JS execution.

- Open URLs, navigate back/forward, reload
- Read page: full text, HTML, all links, selected text
- Run JavaScript in current tab — click, fill, submit, extract
- List, close, or close all tabs
- Take screenshots
- Invoke: `/local-mac-safari` or say "open X in Safari", "read the page", "click the button"
- File: `~/.claude/skills/local-mac-safari/SKILL.md`

> **One-time setup:** Safari → Develop → Allow JavaScript from Apple Events
> (Enable Develop menu: Safari → Settings → Advanced → Show Develop menu)

#### Usage — /local-mac-safari

```text
open https://example.com in Safari
what's the current page title?
list all open tabs
close all tabs
read the page content
get all links on this page
click the submit button
fill the email field with test@example.com
scroll to the bottom of the page
take a screenshot
go back
```

---

### `/local-mac-ssh`

Run commands and manage Docker on pre-authenticated remote workstations.

- Connect by raw `user@ip` or nickname from `ssh_config.sh`
- Run any remote shell command
- Docker: list containers, start/stop, logs, compose up/down/restart, resource stats
- Fetch docker logs → cached to `/tmp/claude` with 10-line preview
- Remote disk usage report (df + du + docker volumes) → cached
- DB dump (Postgres/MySQL) from container → cached as `.sql`
- MySQL read-only queries — `--read-only` connection + keyword blocklist
- Git commands on remote repos (`ssh_git.sh`) — read-only runs immediately, write/destructive require `y` confirmation, subdirs allowed
- Upload local file → remote (`ssh_copy.sh`) — remote dest restricted, overwrite confirmation
- Fetch remote file → local `/tmp/claude` (`ssh_fetch.sh`) — dir-restricted
- Cache cleanup — delete `/tmp/claude` files older than N days
- Runs as a **background subprocess** — Terminal.app is never opened. Output is captured and returned to Claude inline.
- All workstations configured in `ssh_config.sh` — ask, never guess
- Invoke: `/local-mac-ssh` or say "run X on my dev workstation"
- File: `~/.claude/skills/local-mac-ssh/SKILL.md`

#### Usage — /local-mac-ssh

```text
list my workstations
run df -h on dev
show docker containers on dev
fetch docker logs for api-service on dev
what's eating disk on dev
dump the database on dev
run SELECT count(*) FROM users on dev
clean up old cached logs
compose restart worker on dev
```

---

### `/local-mac-network`

Check network status on the local Mac — no Terminal required.

- What process is listening on a port
- Curl an HTTP endpoint (status code + response body)
- Ping a host (reachability + latency)
- DNS lookup (A, AAAA, MX, TXT, CNAME, NS)
- List all TCP/UDP ports currently listening
- File: `~/.claude/skills/local-mac-network/SKILL.md`

#### Usage — /local-mac-network

```text
what's on port 8080?
is my API server running on port 3000?
curl http://localhost:5000/health
ping google.com
dns lookup for github.com
list all open ports
```

---

### `/local-mac-process`

List and manage processes on the local Mac — no Terminal required.

- List all processes or filter by name
- Find what's using a port (delegates to `network_port.sh`)
- Kill a process by PID (graceful TERM, force kill only on request)
- File: `~/.claude/skills/local-mac-process/SKILL.md`

#### Usage — /local-mac-process

```text
is nginx running?
list processes using most CPU
kill process 1234
what process is using port 8080?
```

---

### `/local-mac-docker`

Manage local Docker containers — no Terminal required.

- List all containers (running and stopped)
- View logs snapshot (last N lines, no follow)
- Resource usage snapshot (CPU + memory, no live stream)
- Compose: up, down, restart, stop, ps, logs
- File: `~/.claude/skills/local-mac-docker/SKILL.md`

> For **remote** Docker, use `/local-mac-ssh` instead.

#### Usage — /local-mac-docker

```text
show my local docker containers
logs for api-container last 50 lines
docker stats
compose restart worker
compose down
```

---

### `/local-mac-storage`

Mac storage analysis and cleanup recommendations.

- Shows disk usage breakdown: Library, Downloads, Desktop, Documents, Trash
- Drills into: Library subdirs, Application Support, Caches, Containers
- Recommends safe cleanup: pip cache, brew cache, Docker images, browser caches
- Warns if free space < 5 GB
- Caches report to `.cache/mac-storage-YYYY-MM-DD.md`
- File: `~/.claude/skills/local-mac-storage/SKILL.md`

#### Usage — /local-mac-storage

```text
/local-mac-storage
check my mac storage
what's using disk space?
how much free space do I have?
what's taking up the most space on my Mac?
clean up my disk
show me what I can safely delete
```

| What you get | Details |
| ------------ | ------- |
| Disk status | Total / Used / Available / Capacity % |
| Top space consumers | Sorted by size, flagged if > 1 GB |
| Safe cleanup wins | pip cache, brew cache, Docker images, browser caches |
| Requires-review items | App Support data, Playwright cache, Claude VM bundle |
| Cached report | Written to `.cache/mac-storage-YYYY-MM-DD.md` |

> If free space is under 5 GB, the report leads with a critical warning.

---

### `/local-mac-screencapture`

Screen recording via `screencapture -v` — no Terminal required, no audio.

- Start a recording — auto-named `recording-YYYY-MM-DD-HH-MM-SS.mov`, saved to `~/Movies/Recordings/` by default
- Stop the active recording (sends SIGINT for clean file finalization)
- Check recording status
- List saved recordings
- File: `~/.claude/skills/local-mac-screencapture/SKILL.md`

#### Usage — /local-mac-screencapture

```text
start recording
start recording to ~/Desktop/lectures
stop recording
is recording active?
list my recordings
```

---

### `/local-mac-sync-iphone`

Execute shell commands remotely from your iPhone via iMessage with an explicit confirmation workflow.

- Send commands from iPhone via iMessage to your Mac
- Mac asks for confirmation (YES/OK/CONFIRM) before executing
- Receive command output back via iMessage (auto-split into 150-char chunks)
- Only accepts commands from trusted phone number in `.env`
- Full activity log and state tracking for audit trail
- Confirmation timeout: 5 minutes
- Invoke: `/local-mac-sync-iphone check` or schedule with `/loop`
- File: `~/.claude/skills/local-mac-sync-iphone/SKILL.md`

#### Setup — /local-mac-sync-iphone

1. Create a `.env` file in your working directory:

   ```bash
   PHONE_NUMBER=+1XXXXXXXXXX
   ```

   Replace `+1XXXXXXXXXX` with your actual phone number in E.164 format (e.g., `+14155552671`).

2. Schedule polling (every minute; runs every 10 seconds when scripted directly):

   ```bash
   /loop 1m /local-mac-sync-iphone check
   ```

   Or run manually:

   ```bash
   /local-mac-sync-iphone check
   ```

#### Workflow

1. **Send iMessage from iPhone:**

   ```text
   uptime
   ```

2. **Receive confirmation request on iPhone:**

   ```text
   Command request:

   uptime

   Reply 'YES' to confirm
   ```

3. **Reply YES** (or OK, CONFIRM, CONTINUE)

4. **Receive command output:**

   ```text
   ✓ Command executed:

   10:23:45 up 3 days, 5:10, 2 users, load average: 0.12, 0.08, 0.05
   ```

#### Usage — /local-mac-sync-iphone

```text
/local-mac-sync-iphone check                    # Run one polling cycle manually
/loop 1m /local-mac-sync-iphone check           # Schedule to check every minute
tail -f ~/.imessage-commands.log                # View all activity
cat ~/.imessage-commands-state                  # View pending commands
/schedule --list                                # List active schedules
```

#### Security

- **Phone number whitelist** — Only commands from the number in `.env` are processed
- **Explicit confirmation required** — No auto-execution; every command needs approval
- **Confirmation timeout** — Unapproved commands expire after 5 minutes
- **Audit trail** — All commands, confirmations, and outputs logged to `~/.imessage-commands.log`
- **State file** — `~/.imessage-commands-state` tracks pending approvals (JSON)

> ⚠️ **Use with caution** — This executes arbitrary shell commands on your Mac. Restrict the phone number to a trusted device only.

#### Implementation

- **Script**: `~/workspace/claude_for_mac_local/tools/imessage_command_executor.sh`
- **Dependencies**: `imessage_check.sh`, `imessage_send.sh` from tools directory
- **State file**: `~/.imessage-commands-state` (tracks pending commands with timestamps)
- **Log file**: `~/.imessage-commands.log` (timestamped activity log)
- **Message chunking**: 150 characters per iMessage (works around SMS limits)
- **Confirmation timeout**: 5 minutes (command discarded if not approved in time)
- **Poll interval**: 1 minute via `/loop` (or configurable via `bash` directly every 10 seconds)
