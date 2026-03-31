# claude_for_mac_local

## Privacy Rules

- **Never include personal data** in any code, comments, or documentation — no real IP addresses, phone numbers, email addresses, SSH credentials, API keys, or usernames.
- Use placeholders only: `user@example.com`, `+1XXXXXXXXXX`, `192.168.x.x`, `YOUR_IP`, `xxxxxxxx`.

## Pre-Commit Guardrail: Check for Personal Data

**Use the automated scanning tool:**

```bash
# Scan entire codebase for personal data patterns
./tools/scan_personal_data.sh

# Scan specific directory
./tools/scan_personal_data.sh ./src
```

The tool checks for:

- **Phone numbers** — Indian format (+91XXXXXXXXXX)
- **Email addresses** — non-placeholder patterns
- **IP addresses** — non-private ranges
- **API keys/tokens** — common exposure patterns

Exits with code 0 if clean, 1 if issues found.

**Manual quick check (if needed):**

```bash
git diff --cached | grep -E '\+91[0-9]{10}|[^x][0-9]{10}|@[a-z]+\.[a-z]+' && echo "⚠️  Personal data found!" || echo "✓ No obvious personal data detected"
```

If personal data is found, **do not commit**. Replace with placeholders first.

## Development Workflow

**Always develop features in a new branch, not on `main`.**

```bash
# Create and switch to a feature branch
git checkout -b feature/description-of-change

# After development and testing, create a PR to merge into main
# Do not commit directly to main
```

**Why:**

- Keeps `main` stable and ready for production
- Allows for code review and testing before merging
- Prevents accidental commits of unfinished features
- Makes it easier to revert changes if needed

## Skills

All skills for this project are installed globally at `~/.claude/skills/` and are available in every Claude Code session.

| Skill | Purpose |
| ----- | ------- |
| `claude-mac-obsidian` | Read/write Obsidian markdown notes with bidirectional links |
| `local-mac-calendar` | Read/create/delete Apple Calendar events |
| `local-mac-cleanup-repo` | Clean repository history by removing commits and pushing verified-clean code |
| `local-mac-contacts` | Search macOS Contacts by name |
| `local-mac-edit-personal-data` | Safely edit config files containing personal data with user consent |
| `local-mac-imessage` | Send and read iMessages via osascript |
| `local-mac-scan-personal-data` | Scan codebase for personal data before push (used by pre-push hook) |
| `local-mac-mail` | Read emails from macOS Mail app |
| `local-mac-notes` | Read/create/delete Apple Notes (Claude folder) |
| `local-mac-reminders` | Read/create/delete Apple Reminders |
| `local-mac-storage` | Check and clean up Mac disk storage |
| `local-mac-summarize-claude-session` | Capture Claude session thinking and summaries to daily Obsidian notes |
| `local-mac-music` | Control iMusic playback and play saved playlists |
| `local-mac-spotify` | Control Spotify playback and play saved playlists |
| `local-mac-safari` | Browse, scrape, automate Safari via AppleScript + JavaScript |
| `local-mac-ssh` | Run commands and manage Docker on remote workstations |
| `local-mac-finder` | Open folders/files, reveal items, list windows, manage files in Finder |
| `local-mac-network` | Port lookup, curl endpoint, ping, DNS lookup, list listening ports |
| `local-mac-process` | List processes, find what's on a port, kill a process (with confirmation) |
| `local-mac-docker` | Local Docker — list containers, logs, stats snapshot, compose operations |
| `local-mac-screencapture` | Record the Mac screen — start, stop, status, list recordings |
| `local-mac-wifi` | Wi-Fi controls — on/off, status, current network, list available networks |
| `local-mac-sleep` | Sleep controls — sleep now, schedule sleep, wind-down (close Safari + apps, WiFi off, sleep) |
| `local-mac-time` | Time — get current time, set an alarm at HH:MM, or start a wait-N-minutes timer |

## Tools Directory

The `tools/` directory contains shell scripts required by all local-mac skills. **Do not delete or move this directory** — skills reference these scripts via absolute paths (`~/workspace/claude_for_mac_local/tools/`).

| Script | Used by |
| ------ | ------- |
| `calendar_add_event.sh` | local-mac-calendar |
| `calendar_delete_event.sh` | local-mac-calendar |
| `calendar_list_events.sh` | local-mac-calendar |
| `contacts_search.sh` | local-mac-contacts |
| `contacts_cache_update.sh` | Contacts cache manager — add/search/list cached contacts with cache-first search |
| `imessage_send.sh` | local-mac-imessage |
| `imessage_check.sh` | local-mac-imessage |
| `mail_list_accounts.sh` | local-mac-mail |
| `mail_fetch_inbox.sh` | local-mac-mail |
| `mail_read_email.sh` | local-mac-mail |
| `notes_add.sh` | local-mac-notes |
| `notes_list.sh` | local-mac-notes |
| `notes_read.sh` | local-mac-notes |
| `notes_delete.sh` | local-mac-notes |
| `obsidian_read.sh` | claude-mac-obsidian (read a note) |
| `obsidian_write.sh` | claude-mac-obsidian (write/update a note) |
| `obsidian_list.sh` | claude-mac-obsidian (list all notes) |
| `obsidian_delete.sh` | claude-mac-obsidian (delete a note with confirmation) |
| `obsidian_links.sh` | claude-mac-obsidian (extract forward links from a note) |
| `obsidian_backlinks.sh` | claude-mac-obsidian (find backlinks to a note) |
| `obsidian_summarize_session.sh` | local-mac-summarize-claude-session (capture session summary to daily note) |
| `reminders_add.sh` | local-mac-reminders |
| `reminders_list.sh` | local-mac-reminders |
| `reminders_delete.sh` | local-mac-reminders |
| `storage_overview.sh` | local-mac-storage |
| `storage_detail.sh` | local-mac-storage |
| `music_control.sh` | local-mac-music |
| `music_play.sh` | local-mac-music |
| `spotify_control.sh` | local-mac-spotify |
| `spotify_play.sh` | local-mac-spotify |
| `finder_read.sh` | local-mac-finder (read front window path, list windows, get selection) |
| `finder_control.sh` | local-mac-finder (open, reveal, mkdir, trash) |
| `safari_control.sh` | local-mac-safari |
| `safari_js.sh` | local-mac-safari |
| `safari_read.sh` | local-mac-safari |
| `ssh_common.sh` | local-mac-ssh — shared `SSH_OPTS` array sourced by all ssh_*.sh scripts |
| `ssh_run.sh` | local-mac-ssh |
| `ssh_logs.sh` | local-mac-ssh (fetch + cache docker logs to `LOG_CACHE_DIR`) |
| `ssh_disk.sh` | local-mac-ssh (remote disk usage report, cached) |
| `ssh_db_dump.sh` | local-mac-ssh (dump Postgres/MySQL DB from container to `LOG_CACHE_DIR`) |
| `ssh_db_query.sh` | local-mac-ssh (run read-only MySQL query in container, cached; blocks destructive SQL) |
| `ssh_git.sh` | local-mac-ssh (git commands on remote repos within REMOTE_DIRS; write/destructive require confirmation) |
| `ssh_copy.sh` | local-mac-ssh (upload any local file → remote, remote dest restricted, overwrite confirmation) |
| `ssh_fetch.sh` | local-mac-ssh (download remote → `LOG_CACHE_DIR`, dir-restricted) |
| `ssh_cache_clean.sh` | local-mac-ssh (delete cached files older than `CACHE_RETENTION_DAYS`) |
| `network_port.sh` | local-mac-network (what's listening on a port) |
| `network_curl.sh` | local-mac-network (HTTP request, status + body) |
| `network_ping.sh` | local-mac-network (ping host, capped at 20 packets) |
| `network_dns.sh` | local-mac-network (DNS lookup, A/MX/TXT/CNAME/NS) |
| `network_listen.sh` | local-mac-network (all listening TCP/UDP ports) |
| `process_list.sh` | local-mac-process (list processes, filter by name) |
| `process_kill.sh` | local-mac-process (kill by PID, y/N confirmation, system PID guard) |
| `docker_local_ps.sh` | local-mac-docker (list all local containers) |
| `docker_local_logs.sh` | local-mac-docker (fetch container logs, no follow) |
| `docker_local_stats.sh` | local-mac-docker (CPU/memory snapshot, --no-stream) |
| `docker_local_compose.sh` | local-mac-docker (compose up/down/restart/stop/ps/logs, confirmation on destructive) |
| `screencapture_control.sh` | local-mac-screencapture (start, stop, status, list recordings) |
| `wifi_control.sh` | local-mac-wifi (status, on, off, current SSID, list available networks) |
| `sleep_control.sh` | local-mac-sleep (now, in N minutes, winddown, status, cancel) |
| `time_control.sh` | local-mac-time (now, alarm HH:MM, wait N minutes) |
| `scan_personal_data.sh` | Security utility — scan codebase for personal data patterns (phone numbers, emails, IPs, API keys) |
| `git_local.sh` | Git wrapper — enforces personal data checks before committing (used by `/gc-gp` skill) |

## Config Files

All config files are plain shell — no Python required.

| File | Used by |
| ---- | ------- |
| `ssh_config.sh` | local-mac-ssh — workstation nicknames, compose path, log tail lines |
| `music_config.sh` | local-mac-music — playlist nicknames → exact Music.app names |
| `spotify_config.sh` | local-mac-spotify — playlist nicknames → Spotify URIs |
| `safari_config.sh` | local-mac-safari — URL allowlist, `DISABLE_ALLOWLIST` flag |

## Contacts Cache Manager

The `contacts_cache_update.sh` tool manages a local contacts cache (`~/.contacts_cache`) that stores frequently used contacts for fast lookup.

**Key Features:**

- **Cache-first search** — searches cached contacts first, then falls back to system Contacts
- **Instant lookup** — cached contacts return results immediately
- **Backup & restore** — automatic backup and restore functionality
- **Local-only** — cache file is git-ignored and never pushed to the remote

**Commands:**

```bash
# Search (checks cache first, then system contacts)
./tools/contacts_cache_update.sh search "John"

# Add contact to cache
./tools/contacts_cache_update.sh add "John" "+1XXXXXXXXXX" mobile

# Add quick-access favorite (alias)
./tools/contacts_cache_update.sh favorite "John" "+1XXXXXXXXXX" "J"

# List all cached contacts and favorites
./tools/contacts_cache_update.sh list

# Show recent iMessage contacts
./tools/contacts_cache_update.sh recent

# Backup/restore cache
./tools/contacts_cache_update.sh backup
./tools/contacts_cache_update.sh restore

# Clear cache (with confirmation)
./tools/contacts_cache_update.sh reset
```

**Cache Location:** `~/.contacts_cache` (git-ignored, local only)

## Project Cache Directory

Project-specific cache files are stored at `~/Documents/claude_cache_data/claude_for_mac_local/` to prevent accidental inclusion in version control.

**Contents:**

- **Mac storage reports** — cached by `local-mac-storage` skill (e.g., `mac-storage-2026-03-31.md`)
- **Contacts database** — SQLite cache of contacts for fast lookup

**Why separate from repo:**

- Cache changes frequently and shouldn't trigger commits
- Prevents large or sensitive cache data from leaking into git history
- Keeps project directory clean and focused on source code

**Note:** This directory is git-ignored and never pushed to remote.
