# claude_for_mac_local

## Privacy Rules

- **Never include personal data** in any code, comments, or documentation — no real IP addresses, phone numbers, email addresses, SSH credentials, API keys, or usernames.
- Use placeholders only: `user@example.com`, `+1XXXXXXXXXX`, `192.168.x.x`, `YOUR_IP`, `xxxxxxxx`.

## Pre-Commit Guardrail: Check for Personal Data

**Before every commit, scan for personal data patterns:**

```bash
# Check for phone numbers (Indian format: +91XXXXXXXXXX or 10-digit)
grep -r '\+91[0-9]\{10\}\|[0-9]\{10\}' --include="*.md" --include="*.sh" --include="*.py" .

# Check for common email patterns (not placeholder emails)
grep -rE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' --include="*.md" --include="*.sh" . | grep -v 'example.com'

# Check for IP addresses (not placeholder ranges like 192.168.x.x)
grep -rE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' --include="*.md" --include="*.sh" . | grep -v '192.168\|172.16\|10.0'

# Check for API keys / tokens (common patterns)
grep -rE '(api[_-]?key|secret|token|password)\s*[=:]\s*["\'][^"\']{10,}' --include="*.sh" --include="*.py" . | grep -v 'PLACEHOLDER\|EXAMPLE\|XXXXXXXXXX'
```

**Or use this quick check before committing:**
```bash
git diff --cached | grep -E '\+91[0-9]{10}|[^x][0-9]{10}|@[a-z]+\.[a-z]+' && echo "⚠️  Personal data found in staged changes!" || echo "✓ No obvious personal data detected"
```

If personal data is found, **do not commit**. Replace with placeholders first.

## Skills

All skills for this project are installed globally at `~/.claude/skills/` and are available in every Claude Code session.

| Skill | Purpose |
| ----- | ------- |
| `local-mac-calendar` | Read/create/delete Apple Calendar events |
| `local-mac-contacts` | Search macOS Contacts by name |
| `local-mac-imessage` | Send and read iMessages via osascript |
| `local-mac-mail` | Read emails from macOS Mail app |
| `local-mac-notes` | Read/create/delete Apple Notes (Claude folder) |
| `local-mac-reminders` | Read/create/delete Apple Reminders |
| `local-mac-storage` | Check and clean up Mac disk storage |
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
| `imessage_send.sh` | local-mac-imessage |
| `imessage_check.sh` | local-mac-imessage |
| `mail_list_accounts.sh` | local-mac-mail |
| `mail_fetch_inbox.sh` | local-mac-mail |
| `mail_read_email.sh` | local-mac-mail |
| `notes_add.sh` | local-mac-notes |
| `notes_list.sh` | local-mac-notes |
| `notes_read.sh` | local-mac-notes |
| `notes_delete.sh` | local-mac-notes |
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

## Config Files

All config files are plain shell — no Python required.

| File | Used by |
| ---- | ------- |
| `ssh_config.sh` | local-mac-ssh — workstation nicknames, compose path, log tail lines |
| `music_config.sh` | local-mac-music — playlist nicknames → exact Music.app names |
| `spotify_config.sh` | local-mac-spotify — playlist nicknames → Spotify URIs |
| `safari_config.sh` | local-mac-safari — URL allowlist, `DISABLE_ALLOWLIST` flag |
