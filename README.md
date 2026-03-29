# local-mac-skills — Claude Code

A collection of **Claude Code skills** that let you control native macOS apps and remote workstations — iMessage, Mail, Calendar, Notes, Reminders, Contacts, Storage, Spotify, and SSH+Docker — entirely through natural language prompts inside Claude Code.

Built-in guardrails enforced at the script level: Notes access is scoped to a dedicated `Claude` folder; Mail and Contacts are read-only; SSH connections are restricted to an explicit host allowlist; destructive SSH commands (`rm -rf`, `docker system prune`) require confirmation; database queries are read-only via `--read-only` flag plus a local SQL keyword block; iMessage send confirms ambiguous recipients; Spotify and iMusic are playback-only with no URI guessing.

---

## What is a Claude Code Skill?

A skill is a `SKILL.md` file placed in `~/.claude/skills/<skill-name>/`. Claude Code loads it automatically and maps natural language prompts to shell scripts on your machine. No plugins, no cloud calls — just AppleScript + bash running locally.

---

## Highlight — iMusic Control

> **Control iMusic without leaving Claude Code.**

Play playlists by nickname, skip tracks, adjust volume — via AppleScript. No API, no URI hunting. Playlist names map directly from your library.

```text
play focus playlist
pause music
next track
what's playing?
set volume to 60
```

→ [View skill definition](skills/local-mac-music/SKILL.md)

---

## Highlight — Spotify Control

> **Control Spotify without leaving Claude Code.**

Play saved playlists, skip tracks, adjust volume — all via natural language. No API token, no OAuth. Pure AppleScript. One-time setup: paste your playlist URIs into `spotify_config.py`.

```text
play focus playlist
pause spotify
next track
what's playing?
set volume to 60
```

→ [View skill definition](skills/local-mac-spotify/SKILL.md)

---

## Highlight — Remote Dev via SSH + Docker

> **Talk to your remote workstations in plain English.**

If you run your development stack on a remote workstation (Docker Compose, containers, services), this skill lets you manage it entirely through Claude Code — no terminal tab-switching, no typing raw SSH commands.

**Save your workstation once:**

```text
save host dev as ubuntu@192.168.1.10
```

**Then just ask:**

```text
show docker containers on dev
docker logs api-service on dev
compose restart worker on dev
copy logs of nginx on dev
run free -h on dev
```

Works with any pre-authenticated SSH machine (key-based auth, no passwords). Uses `BatchMode=yes` — never hangs. Destructive commands like `docker system prune` always ask for confirmation first.

→ [View skill definition](skills/local-mac-ssh/SKILL.md)

---

## Skills

→ [Full skills reference](wiki/SKILLS_WIKI.md)

---

## Prompts

These are real prompts you can type directly into Claude Code once the skills are installed.

### iMessage

**Send messages:**

```text
send "Hey, on my way!" to +1XXXXXXXXXX
send an iMessage to user@example.com saying "Meeting rescheduled to 3pm"
send a message to +91XXXXXXXXXX after 5 minutes saying "Call me back"
```

**Check messages:**

```text
check messages from the last 30 minutes
show iMessages received in the last hour
check all messages from +91XXXXXXXXXX in the last 2 hours
```

**Configuration (optional):**

Copy `.env.example` to `.env` and set your default phone number for quick message checks:

```bash
cp .env.example .env
# Edit .env and set IMESSAGE_PHONE_NUMBER=your_number
```

### Mail

```text
check last 5 emails from iCloud
show 10 emails from my Gmail
read email 3
```

### Calendar

```text
show my calendar for this week
what do I have tomorrow?
add event "Team standup" on Monday at 10am
add event "Dentist" on Friday at 2pm for 1 hour
delete event "Old meeting"
```

### Notes

```text
list my notes
show note "Meeting summary"
add note "Ideas" — launch in Q3, redesign onboarding
delete note "Old draft"
search notes for "budget"
```

### Reminders

```text
show my pending reminders
show all reminders from the Home list
add reminder "Call dentist" due Friday at 10am
add reminder "Pay rent" due 1st of next month
delete reminder "Buy groceries"
```

### Contacts

```text
find contact John
look up Sarah's phone number
search for "Doe" with email
```

### Storage

```text
check my Mac storage
what's using disk space?
/local-mac-storage
how much free space do I have?
```

### iMusic

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

### Spotify

```text
play focus playlist
pause spotify
next track
previous track
what's playing?
set volume to 70
```

### Safari

```text
open https://example.com in Safari
what's the current page title?
list all open tabs
read the page content
get all links on this page
click the submit button
fill in the email field with test@example.com
take a screenshot of the current page
go back
```

### SSH + Docker

```text
save host dev as ubuntu@192.168.1.10
run df -h on dev
show docker containers on dev
docker logs api-service on dev
copy logs of nginx on dev
compose restart worker on dev
compose up on ubuntu@10.0.0.5
```

---

## Guardrails

Each skill has built-in restrictions enforced at both the instruction level and the shell script level.

→ [Full guardrails reference](wiki/GUARDRAILS_WIKI.md)

---

## Configuration

Config files live at the **root of the repo**. All are plain shell files — open in any text editor, uncomment lines, and save.

### `ssh_config.sh` — remote workstations

```bash
SSH_dev_host="ubuntu@192.168.1.10"
SSH_dev_desc="Local dev workstation"
LOG_TAIL_LINES=50
COMPOSE_PATH="/home/ubuntu/myapp"
```

### `music_config.sh` — iMusic playlists

```bash
PLAYLIST_focus="Deep Focus"    # exact name as it appears in Music.app
PLAYLIST_chill="Chill Vibes"
```

### `spotify_config.sh` — Spotify playlists

```bash
PLAYLIST_focus="spotify:playlist:xxxxxxxx"
PLAYLIST_chill="spotify:playlist:xxxxxxxx"
```

Get a Spotify URI: right-click any playlist in Spotify → Share → Copy Spotify URI.

### `safari_config.sh` — allowed URLs

```bash
DISABLE_ALLOWLIST=false
ALLOWED_URLS=(
    "google.com"
    "github.com"
)
```

---

## Installation

### 1. Clone the repo

```bash
git clone git@github.com:debaditya-mohankudo/local-mac-skills-Claude-Code.git ~/workspace/claude_for_mac_local
```

### 2. Install skills globally

```bash
cp -r ~/workspace/claude_for_mac_local/skills/* ~/.claude/skills/
```

### 3. Make tool scripts executable

```bash
chmod +x ~/workspace/claude_for_mac_local/tools/*.sh
```

### 4. Grant permissions (first use)

Some skills require macOS permissions:

| Skill | Permission needed |
| ----- | ----------------- |
| iMessage (send) | Accessibility — System Settings → Privacy & Security → Accessibility |
| iMessage (read) | Full Disk Access — System Settings → Privacy & Security → Full Disk Access |
| Mail | Automation — grant when prompted on first run |
| Calendar | Calendars — grant when prompted on first run |
| Notes | Automation — grant when prompted on first run |
| Reminders | Reminders — grant when prompted on first run |
| Contacts | Contacts — grant when prompted on first run |
| Spotify | Automation — grant when prompted on first run |

---

## Structure

```text
.
├── skills/                  # Skill definitions (copy to ~/.claude/skills/)
│   ├── local-mac-calendar/
│   ├── local-mac-contacts/
│   ├── local-mac-imessage/
│   ├── local-mac-mail/
│   ├── local-mac-notes/
│   ├── local-mac-reminders/
│   ├── local-mac-storage/
│   ├── local-mac-music/
│   ├── local-mac-safari/
│   ├── local-mac-spotify/
│   └── local-mac-ssh/
├── tools/                   # Shell scripts called by skills
│   ├── imessage_send.sh
│   ├── imessage_check.sh
│   ├── mail_fetch_inbox.sh
│   ├── calendar_list_events.sh
│   ├── calendar_add_event.sh
│   ├── calendar_delete_event.sh
│   ├── notes_list.sh
│   ├── notes_add.sh
│   ├── notes_read.sh
│   ├── notes_delete.sh
│   ├── reminders_list.sh
│   ├── reminders_add.sh
│   ├── reminders_delete.sh
│   ├── contacts_search.sh
│   ├── storage_overview.sh
│   ├── storage_detail.sh
│   ├── music_control.sh
│   ├── music_play.sh
│   ├── safari_control.sh
│   ├── safari_js.sh
│   ├── safari_read.sh
│   ├── spotify_control.sh
│   ├── spotify_play.sh
│   ├── ssh_run.sh
│   └── ...
├── ssh_config.sh            # SSH workstation list + defaults
├── music_config.sh          # iMusic playlist nicknames
├── spotify_config.sh        # Spotify playlist nicknames
├── safari_config.sh         # Safari URL allowlist
├── wiki/                    # Reference docs
│   ├── SKILLS_WIKI.md       # Detailed skill reference
│   ├── TOOLS_WIKI.md        # Shell script reference
│   ├── GUARDRAILS_WIKI.md   # Guardrails reference for all skills
│   └── FUTURE_SKILLS.md     # Planned skills roadmap
└── CLAUDE.md                # Claude Code project instructions
```

---

## IDE Support

These skills work in any environment where Claude Code runs. Supported IDEs:

| IDE / Editor | How to use |
| ------------ | ---------- |
| **VS Code** (v1.98+) | Install the Claude Code extension — full graphical panel with diffs and checkpoints |
| **Cursor** | Same as VS Code — uses the VS Code extension |
| **JetBrains** (IntelliJ, PyCharm, WebStorm, GoLand, Android Studio, PhpStorm) | Install the Claude Code plugin — runs via the integrated terminal |
| **Chrome / Edge** | Claude in Chrome extension — browser automation via `@browser` or `--chrome` flag |
| **Terminal (any)** | Run `claude` directly — all skills work the same way |

---

## Requirements

- macOS (Apple Silicon or Intel)
- [Claude Code](https://claude.ai/claude-code) CLI installed
- `osascript` (built into macOS)
- `sqlite3` (built into macOS, used by iMessage read)
- `bash` and standard Unix tools

---

## Contributing

PRs welcome. Each skill lives in `skills/<name>/SKILL.md` — the format is plain markdown with a YAML frontmatter block. Shell tools go in `tools/`.
