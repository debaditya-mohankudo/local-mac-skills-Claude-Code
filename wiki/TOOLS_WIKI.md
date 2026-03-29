# Tools Wiki

Standalone bash scripts in `tools/` for macOS automation. All scripts are executable and can be run directly from terminal.

**Last updated:** 2026-03-22

---

## Usage convention

```text
./tools/<script>.sh [ARGS]
```

Arguments with spaces should be quoted. Optional args are shown in `[brackets]`.

---

## iMessage

### `imessage_send.sh`

Send an iMessage to a phone number or Apple ID email.

```text
./tools/imessage_send.sh RECIPIENT MESSAGE

./tools/imessage_send.sh "+91XXXXXXXXXX" "Hello from Claude"
./tools/imessage_send.sh "user@example.com" "Good morning"
```

---

### `imessage_check.sh`

Read iMessages from the last N minutes (default: 30).

> ⏳ PENDING — requires Full Disk Access for terminal app in System Settings → Privacy & Security

```text
./tools/imessage_check.sh [MINUTES]

./tools/imessage_check.sh        # last 30 min
./tools/imessage_check.sh 60     # last 60 min
```

---

## Mail

### `mail_list_accounts.sh`

List all accounts configured in macOS Mail with their email addresses.

```text
./tools/mail_list_accounts.sh
```

---

### `mail_fetch_inbox.sh`

Fetch the latest N emails from a Mail account's INBOX (default: 5).

```text
./tools/mail_fetch_inbox.sh ACCOUNT_NAME [N]

./tools/mail_fetch_inbox.sh Google 10
./tools/mail_fetch_inbox.sh iCloud
```

---

### `mail_read_email.sh`

Read the full content of an email by its position in the INBOX.

```text
./tools/mail_read_email.sh ACCOUNT_NAME INDEX

./tools/mail_read_email.sh Google 3
```

---

## Calendar

### `calendar_list_events.sh`

List all calendar events between two dates. Skips system calendars (Birthdays, Siri Suggestions, Vedic Astro Events).

Date format: `MM/DD/YYYY HH:MM:SS`

```text
./tools/calendar_list_events.sh START_DATE END_DATE

./tools/calendar_list_events.sh "03/21/2026 00:00:00" "03/28/2026 23:59:59"
```

---

### `calendar_add_event.sh`

Add a new event to a calendar.

```text
./tools/calendar_add_event.sh CALENDAR TITLE START END [NOTES]

./tools/calendar_add_event.sh "Work" "Team standup" "03/24/2026 10:00:00" "03/24/2026 10:30:00"
./tools/calendar_add_event.sh "Work" "Doctor" "03/25/2026 11:00:00" "03/25/2026 12:00:00" "Annual checkup"
```

---

### `calendar_delete_event.sh`

Delete a calendar event by exact title.

```text
./tools/calendar_delete_event.sh CALENDAR "EXACT TITLE"

./tools/calendar_delete_event.sh "Work" "Team standup"
```

---

## Notes

All notes scripts operate on the **"Claude"** folder in Apple Notes only.

### `notes_list.sh`

List all notes with modification date and a 120-character body preview.

```text
./tools/notes_list.sh
```

---

### `notes_add.sh`

Create a new note in the Claude folder.

```text
./tools/notes_add.sh "TITLE" "BODY"

./tools/notes_add.sh "Grocery list" "Milk, eggs, bread"
```

---

### `notes_read.sh`

Read the full plaintext of a note.

```text
./tools/notes_read.sh "TITLE"

./tools/notes_read.sh "Grocery list"
```

---

### `notes_delete.sh`

Delete a note by exact title.

```text
./tools/notes_delete.sh "EXACT TITLE"

./tools/notes_delete.sh "Old draft"
```

---

## Reminders

### `reminders_list.sh`

List reminders across all lists. Filter by status: `all` (default), `pending`, `completed`.

```text
./tools/reminders_list.sh [STATUS]

./tools/reminders_list.sh
./tools/reminders_list.sh pending
./tools/reminders_list.sh completed
```

---

### `reminders_add.sh`

Add a reminder to a list with optional due date and notes.

Date format: `MM/DD/YYYY HH:MM:SS`

```text
./tools/reminders_add.sh LIST "NAME" ["DUE_DATE"] ["NOTES"]

./tools/reminders_add.sh "Reminders" "Buy milk"
./tools/reminders_add.sh "Reminders" "Call dentist" "03/25/2026 10:00:00"
./tools/reminders_add.sh "Home" "Fix tap" "" "Kitchen sink"
```

---

### `reminders_delete.sh`

Delete a reminder by exact name from a list.

```text
./tools/reminders_delete.sh LIST "EXACT NAME"

./tools/reminders_delete.sh "Reminders" "Buy milk"
```

---

## Contacts

### `contacts_search.sh`

Search macOS Contacts by name. Pass `--with-email` to also return email addresses.

```text
./tools/contacts_search.sh "NAME" [--with-email]

./tools/contacts_search.sh "John"
./tools/contacts_search.sh "John" --with-email
```

---

## SSH

### `ssh_common.sh` — shared connection options

All `ssh_*.sh` scripts source this file to get a consistent `SSH_OPTS` / `SCP_OPTS` array. Key options:

| Option | Value | Purpose |
| --- | --- | --- |
| `BatchMode` | `yes` | Disables password prompts — fails fast if key auth is missing |
| `ConnectTimeout` | `10` | Aborts if the host doesn't respond within 10 seconds |
| `StrictHostKeyChecking` | `accept-new` | Auto-accepts new host keys; rejects changed ones (TOFU) |
| `ControlMaster` | `auto` | First connection creates a master socket; subsequent ones reuse it |
| `ControlPath` | `/tmp/ssh_mux_%r@%h:%p` | One socket per `user@host:port` — multiple machines are independent |
| `ControlPersist` | `60` | Keeps the master socket alive 60s after the last connection closes |

**Performance — ControlMaster connection reuse (measured locally, Docker sandbox):**

| Connection type | Time | Notes |
| --- | --- | --- |
| Cold (first call, full handshake) | ~75ms | Key exchange + TCP setup |
| Warm (socket reuse) | ~10ms | Skips handshake entirely |
| Speedup | **~7.5×** | More pronounced on remote hosts over WAN |

Each unique `user@host:port` gets its own socket — connecting to multiple machines is fully independent.

---

### `ssh_run.sh`

Run any command on a pre-authenticated remote SSH host.

```text
./tools/ssh_run.sh USER@IP "COMMAND"

./tools/ssh_run.sh ubuntu@192.168.1.10 "df -h"
./tools/ssh_run.sh ubuntu@192.168.1.10 "docker ps -a"
```

---

### `ssh_logs.sh`

Fetch docker logs from a remote container and cache to `LOG_CACHE_DIR` (`/tmp/claude`). Prints a 10-line preview and the path to the cached file.

```text
./tools/ssh_logs.sh USER@IP CONTAINER [TAIL_LINES]

./tools/ssh_logs.sh ubuntu@192.168.1.10 api-service
./tools/ssh_logs.sh ubuntu@192.168.1.10 api-service 200
```

Output filename: `<host>_<container>_tail<N>_<timestamp>.log`

---

### `ssh_disk.sh`

Fetch a disk usage report from a remote host — `df -h`, top directories by size, and docker volume usage. Caches result to `LOG_CACHE_DIR`.

```text
./tools/ssh_disk.sh USER@IP

./tools/ssh_disk.sh ubuntu@192.168.1.10
```

Output filename: `<host>_disk_<timestamp>.txt`

---

### `ssh_db_dump.sh`

Dump a Postgres or MySQL database from a remote Docker container to `LOG_CACHE_DIR`. Falls back to `ssh_config.sh` defaults for any omitted arguments.

```text
./tools/ssh_db_dump.sh USER@IP [CONTAINER] [DB_NAME] [DB_USER] [DB_TYPE]

./tools/ssh_db_dump.sh ubuntu@192.168.1.10
./tools/ssh_db_dump.sh ubuntu@192.168.1.10 mysql-container mydb root mysql
./tools/ssh_db_dump.sh ubuntu@192.168.1.10 postgres-container mydb postgres postgres
```

Output filename: `<host>_<container>_<db>_dump_<timestamp>.sql`

---

### `ssh_db_query.sh`

Run a MySQL query inside a remote Docker container. Uses a read-only MySQL connection (`--read-only`). Caches result to `LOG_CACHE_DIR`.

**Guardrail:** `DROP`, `ALTER`, `TRUNCATE`, `DELETE`, `RENAME`, `CREATE`, `REPLACE` are blocked locally before SSH connects.

```text
./tools/ssh_db_query.sh USER@IP "SQL" [CONTAINER] [DB_NAME] [DB_USER]

./tools/ssh_db_query.sh ubuntu@192.168.1.10 "SELECT count(*) FROM users"
./tools/ssh_db_query.sh ubuntu@192.168.1.10 "SHOW TABLES" mysql-container mydb root
```

Output filename: `<host>_<container>_query_<timestamp>.txt`

---

### `ssh_git.sh`

Run git commands on a remote repository. Repo must be a nickname or path within `REMOTE_DIRS` in `ssh_config.sh`. Subdirectories are automatically allowed. Read-only commands run directly; write/destructive commands require `y` confirmation before SSH connects. Result is cached to `LOG_CACHE_DIR`.

**Guardrail:** Write/destructive git subcommands require explicit confirmation at the script level before SSH connects.

```text
./tools/ssh_git.sh USER@IP "GIT COMMAND" [REPO]

# Read-only (run immediately, SSH connects)
./tools/ssh_git.sh ubuntu@192.168.1.10 "log --oneline -20" app
./tools/ssh_git.sh ubuntu@192.168.1.10 "status" app
./tools/ssh_git.sh ubuntu@192.168.1.10 "diff HEAD~1" app/api
./tools/ssh_git.sh ubuntu@192.168.1.10 "branch -a" app
./tools/ssh_git.sh ubuntu@192.168.1.10 "stash list" app

# Write/destructive (prompts y/N before SSH connects)
./tools/ssh_git.sh ubuntu@192.168.1.10 "add ." app
./tools/ssh_git.sh ubuntu@192.168.1.10 "commit -m 'message'" app
./tools/ssh_git.sh ubuntu@192.168.1.10 "push" app
./tools/ssh_git.sh ubuntu@192.168.1.10 "reset --hard HEAD~1" app
```

Read-only: `status`, `log`, `diff`, `branch`, `show`, `stash list`, `remote -v`, `tag`, `describe`, `shortlog`, `rev-parse`, `blame`

Write/destructive (require confirmation): `commit`, `push`, `pull`, `merge`, `rebase`, `reset`, `checkout`, `fetch`, `add`, `rm`, `mv`, `stash pop/apply/drop`, `branch -d/-D/-m`, `tag -a/-d/-f`, `clean`, `restore`, `init`, `clone`, `gc`, `prune`

Output filename: `<host>_git_<command>_<timestamp>.txt`

---

### `ssh_copy.sh`

Upload any local file to a remote directory over SCP. Local source is unrestricted. Remote destination is validated against `REMOTE_DIRS` in `ssh_config.sh`. Supports `nickname:path` syntax.

**Guardrail:** Warns and asks confirmation before overwriting an existing file on remote.

```text
./tools/ssh_copy.sh USER@IP LOCAL_SRC REMOTE_DEST

./tools/ssh_copy.sh ubuntu@192.168.1.10 "tmp:report.txt" "app:"
./tools/ssh_copy.sh ubuntu@192.168.1.10 "downloads:data.csv" "home:"
./tools/ssh_copy.sh ubuntu@192.168.1.10 /tmp/claude/file.sh /home/ubuntu/
```

Set `DISABLE_DIR_RESTRICTION=true` in `ssh_config.sh` to allow arbitrary paths (not recommended).

---

### `ssh_fetch.sh`

Download a file from a remote host to `LOG_CACHE_DIR` (`/tmp/claude`). Remote path validated against `REMOTE_DIRS` in `ssh_config.sh`. Supports `nickname:path` syntax.

```text
./tools/ssh_fetch.sh USER@IP REMOTE_SRC

./tools/ssh_fetch.sh ubuntu@192.168.1.10 "tmp:error.log"
./tools/ssh_fetch.sh ubuntu@192.168.1.10 "app:logs/access.log"
./tools/ssh_fetch.sh ubuntu@192.168.1.10 /tmp/output.txt
```

Output filename: `<host>_<filename>_<timestamp>.<ext>` in `LOG_CACHE_DIR`.

---

### `ssh_cache_clean.sh`

Delete files in `LOG_CACHE_DIR` older than N days. Defaults to `CACHE_RETENTION_DAYS` from `ssh_config.sh` (default: 7).

```text
./tools/ssh_cache_clean.sh [DAYS]

./tools/ssh_cache_clean.sh       # use config default
./tools/ssh_cache_clean.sh 3     # delete files older than 3 days
```

---

## Storage

### `storage_overview.sh`

Show disk usage summary and top-level home directory sizes.

```text
./tools/storage_overview.sh
```

---

### `storage_detail.sh`

Detailed breakdown of Library subdirectories, Application Support, Caches, and Containers.

```text
./tools/storage_detail.sh
```

---

## Cleanup

### `safe_to_del.sh`

One-shot Mac storage cleanup. Purges pip cache, Homebrew cache, browser caches (Edge, Firefox, Zoho, Zoom, Telegram), Playwright cache, and optionally all Docker images.

```text
./tools/safe_to_del.sh
```

- Prompts before running `docker system prune -a`
- Shows disk status before and after
- Note: Claude VM bundle (11 GB) must be removed via Claude app Settings

---

### `ollama_cleanup.sh`

Clean up local Ollama models interactively. Lists all models with sizes, then offers options to remove all, select specific models, or remove models unused for 90+ days.

```text
./tools/ollama_cleanup.sh [--all] [--dry-run]

./tools/ollama_cleanup.sh            # interactive mode
./tools/ollama_cleanup.sh --all      # remove all models non-interactively
./tools/ollama_cleanup.sh --dry-run  # preview what would be removed
```

---

### `docker_cleanup.sh`

Docker cleanup with guardrails. Steps through each resource type with confirmation prompts:

1. Stopped containers
2. Dangling (untagged) images
3. All unused images
4. Unused volumes *(irreversible — warns before proceeding)*
5. Build cache
6. Docker.raw VM disk compaction (Apple Silicon: recommends Docker Desktop UI)

```text
./tools/docker_cleanup.sh
```

---

## Network

### `network_port.sh`

Show what process is listening on a given port (TCP and UDP).

```text
./tools/network_port.sh PORT

./tools/network_port.sh 8080
./tools/network_port.sh 5432
```

---

### `network_curl.sh`

Perform an HTTP request and return status code + response body (truncated to 3000 chars).

```text
./tools/network_curl.sh URL [METHOD] [DATA]

./tools/network_curl.sh http://localhost:3000/health
./tools/network_curl.sh http://localhost:3000/api/users GET
./tools/network_curl.sh http://localhost:3000/api/login POST '{"user":"test"}'
```

Warns before any non-GET/HEAD request. 15s timeout.

---

### `network_ping.sh`

Ping a host and report reachability and average latency.

```text
./tools/network_ping.sh HOST [COUNT]

./tools/network_ping.sh google.com
./tools/network_ping.sh 192.168.x.x 10
```

COUNT defaults to 4, capped at 20.

---

### `network_dns.sh`

DNS lookup for a host.

```text
./tools/network_dns.sh HOST [TYPE]

./tools/network_dns.sh github.com
./tools/network_dns.sh github.com MX
./tools/network_dns.sh github.com TXT
```

TYPE defaults to `A`. Allowed: `A`, `AAAA`, `MX`, `TXT`, `CNAME`, `NS`, `PTR`, `SOA`.

---

### `network_listen.sh`

List all TCP/UDP ports currently listening on this machine with process names.

```text
./tools/network_listen.sh
```

---

## Process

### `process_list.sh`

List running processes. With a name filter, shows only matching processes. Without, shows top 30 by CPU.

```text
./tools/process_list.sh [NAME]

./tools/process_list.sh          # top 30 by CPU
./tools/process_list.sh nginx    # processes matching "nginx"
./tools/process_list.sh python
```

---

### `process_kill.sh`

Kill a process by PID. Always confirms with y/N before sending the signal.

```text
./tools/process_kill.sh PID [SIGNAL]

./tools/process_kill.sh 1234
./tools/process_kill.sh 1234 9    # force kill
```

SIGNAL defaults to `TERM`. Blocks PID < 100 and critical system processes.

---

## Local Docker

### `docker_local_ps.sh`

List all local Docker containers (running and stopped).

```text
./tools/docker_local_ps.sh
```

---

### `docker_local_logs.sh`

Fetch the last N lines of logs from a local container (no `--follow`).

```text
./tools/docker_local_logs.sh CONTAINER [LINES]

./tools/docker_local_logs.sh api-service
./tools/docker_local_logs.sh api-service 200
```

---

### `docker_local_stats.sh`

Snapshot of CPU/memory for all containers or one specific container. Uses `--no-stream`.

```text
./tools/docker_local_stats.sh [CONTAINER]

./tools/docker_local_stats.sh
./tools/docker_local_stats.sh api-service
```

---

### `docker_local_compose.sh`

Run docker compose operations with confirmation on destructive actions.

```text
./tools/docker_local_compose.sh ACTION [SERVICE] [PATH]

./tools/docker_local_compose.sh ps
./tools/docker_local_compose.sh up worker
./tools/docker_local_compose.sh restart worker /home/user/myapp
./tools/docker_local_compose.sh down           # asks y/N
./tools/docker_local_compose.sh logs api
```

Actions: `up`, `down`, `restart`, `stop`, `ps`, `logs`. PATH defaults to current directory.

---

## Screen Recording

### `screencapture_control.sh`

Start, stop, check status, and list screen recordings. No audio. Recordings auto-named by date/time.

```text
./tools/screencapture_control.sh start [output_dir]
./tools/screencapture_control.sh stop
./tools/screencapture_control.sh status
./tools/screencapture_control.sh list [output_dir]
```

Default output dir: `~/Movies/Recordings/`. Only one recording can be active at a time.

---

## Music

### `music_control.sh`

Control iMusic playback — play, pause, skip, volume, and current track info.

```text
./tools/music_control.sh COMMAND [VALUE]

./tools/music_control.sh play
./tools/music_control.sh pause
./tools/music_control.sh next
./tools/music_control.sh previous
./tools/music_control.sh volume 70
./tools/music_control.sh current
```

Commands: `play`, `pause`, `next`, `previous`, `volume` (requires VALUE 0–100), `current`

---

### `music_play.sh`

Play a playlist by its exact name in Music.app.

```text
./tools/music_play.sh "PLAYLIST NAME"

./tools/music_play.sh "Focus"
./tools/music_play.sh "Chill Mix"
```

Playlist name must match exactly as it appears in Music.app (case-sensitive). Configure nicknames → exact names in `music_config.sh`.

---

## Spotify

### `spotify_control.sh`

Control Spotify playback — play, pause, skip, volume, and current track info.

```text
./tools/spotify_control.sh COMMAND [VALUE]

./tools/spotify_control.sh play
./tools/spotify_control.sh pause
./tools/spotify_control.sh next
./tools/spotify_control.sh previous
./tools/spotify_control.sh volume 70
./tools/spotify_control.sh current
```

Commands: `play`, `pause`, `next`, `previous`, `volume` (requires VALUE 0–100), `current`

---

### `spotify_play.sh`

Play a Spotify URI (track, playlist, or album).

```text
./tools/spotify_play.sh SPOTIFY_URI

./tools/spotify_play.sh "spotify:playlist:37i9dQZF1DX0XUsuxWHRQd"
```

Get a URI: right-click any item in Spotify → Share → Copy Spotify URI. Configure nickname → URI mappings in `spotify_config.sh`.

---

## Finder

### `finder_read.sh`

Read Finder state — front window path, all open windows, selected items.

```text
./tools/finder_read.sh front-path    # POSIX path of the front Finder window
./tools/finder_read.sh list-windows  # all open windows with paths
./tools/finder_read.sh selection     # POSIX paths of currently selected items
```

---

### `finder_control.sh`

Open, reveal, create, and trash items via Finder AppleScript.

```text
./tools/finder_control.sh open PATH    # open a folder or file in Finder
./tools/finder_control.sh reveal PATH  # select an item in its parent folder
./tools/finder_control.sh mkdir PATH   # create folder + reveal it (HOME only)
./tools/finder_control.sh trash PATH   # move to Trash (y/N confirmation)
```

**Guardrails:**

- `open` / `reveal` — path must exist, error otherwise
- `mkdir` — restricted to `$HOME` subtree; system paths blocked
- `trash` — requires explicit `y` at the prompt; item goes to `~/.Trash` (recoverable)

---

## Safari

### `safari_control.sh`

Navigate and control Safari tabs via AppleScript.

```text
./tools/safari_control.sh open "https://example.com"
./tools/safari_control.sh current-url
./tools/safari_control.sh current-title
./tools/safari_control.sh list-tabs
./tools/safari_control.sh close-tab
./tools/safari_control.sh reload
./tools/safari_control.sh back
./tools/safari_control.sh forward
./tools/safari_control.sh screenshot [/tmp/output.png]
```

---

### `safari_js.sh`

Execute JavaScript in the current Safari tab and return the result.

> Requires: Safari → Develop → Allow JavaScript from Apple Events

```text
./tools/safari_js.sh "document.title"
./tools/safari_js.sh "document.querySelector('h1').innerText"
./tools/safari_js.sh "document.querySelector('input[name=q]').value = 'hello'"
./tools/safari_js.sh "document.querySelector('button.submit').click()"
```

---

### `safari_read.sh`

Read content from the current Safari tab.

```text
./tools/safari_read.sh text       # full page innerText
./tools/safari_read.sh html       # full page outerHTML
./tools/safari_read.sh links      # all links (href + label)
./tools/safari_read.sh title      # document title
./tools/safari_read.sh selected   # currently selected text
```
