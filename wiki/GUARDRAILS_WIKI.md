# Guardrails Wiki

Each skill has built-in restrictions enforced at the skill instruction level and, where possible, at the shell script level. Claude will not act outside these boundaries. This document is the authoritative reference for all guardrails across every skill and tool.

**Last updated:** 2026-03-29 — added iMessage ALLOWED_PHONE_NUMBERS allowlist guardrail

---

## Design Principle

> **Add a guardrail if it is easy to implement.**

Low-cost safety rails are always worth adding. Guardrails in this project take two forms:

1. **Instruction-level** — rules in `SKILL.md` that Claude follows as part of the prompt.
2. **Script-level** — checks in shell scripts (`tools/*.sh`) that enforce limits regardless of what Claude decides. Script-level guardrails are stronger because they cannot be overridden by a confused or manipulated prompt.

When both forms are possible for a given risk, both are implemented.

---

## Skill Guardrails

### Notes — folder-scoped

**Risk:** Accidentally reading, modifying, or deleting personal notes outside the intended scope.

**Guardrails:**

- Only the `Claude` folder in Notes.app is accessible. Notes in Personal, iCloud root, or any other folder are never touched.
- Read, create, and delete operations are all scoped to this folder.
- You must create a folder named `Claude` in Notes.app before using the skill.

**Why this scope:** Notes.app holds personal and sensitive content. Limiting Claude to one dedicated folder prevents any accidental access to unrelated notes.

---

### Calendar — calendar-scoped + system calendar exclusions

**Risk:** Creating or deleting events on the wrong calendar, or reading noise from system-managed calendars.

**Guardrails:**

- Default calendar is `Work` — all read, add, and delete operations target this calendar unless you name a different one explicitly.
- The following system calendars are **always skipped** unless explicitly requested:
  - `Birthdays`
  - `Siri Suggestions`
  - `Scheduled Reminders`
  - `Vedic Astro Events`
  - `Drik Panchang`
- Claude will not delete an event without showing what it found and asking for confirmation if the match is ambiguous.

**Why this scope:** System calendars are auto-managed by macOS and should not be written to. The `Work` default prevents events landing in unexpected places.

---

### Mail — read-only, inbox only

**Risk:** Unintended email actions (send, delete, move, mark as read).

**Guardrails:**

- **Read-only** — the skill cannot send, delete, move, or flag emails. No write access at all.
- Only reads the **INBOX** mailbox of the specified account — no other folders.
- Email body content is **truncated to 2000 characters** to prevent context overload.
- If no account email is specified in the prompt, Claude asks before fetching anything.

**Why read-only:** Email actions are high-stakes and hard to reverse. Read access for summarization and triage is the safe default; write access would require explicit opt-in tooling not currently built.

---

### iMessage — send only, explicit recipient required, allowlist-enforced

**Risk:** Sending messages to unintended recipients, or reading private message history.

**Guardrails (script-level, enforced in `imessage_send.sh`):**

- **Recipient allowlist** — if `ALLOWED_PHONE_NUMBERS` is set in `.env`, the script validates every recipient against this comma-separated list **before sending**. Any recipient not on the list is rejected with an error and the message is never sent.
- **Send only** — the skill sends via `osascript` which does not expose read access to chat history.
- Reading chat history via `imessage_check.sh` requires **Full Disk Access** explicitly granted by the user — the skill will not attempt it without that permission being in place.
- Claude will always echo the recipient and message content before sending and ask for confirmation if the request is ambiguous.
- Messages app must be open and signed into iMessage for sending to work.

**How to configure the allowlist:**

```bash
# .env
ALLOWED_PHONE_NUMBERS=+91XXXXXXXXXX,+91XXXXXXXXXX,user@example.com
```

- Comma-separated list of phone numbers and/or Apple ID emails
- Phone numbers should be in E.164 format (e.g. `+91XXXXXXXXXX`)
- Whitespace around entries is automatically trimmed
- If not set or empty, no allowlist validation is enforced (all recipients allowed)

**Why script-level enforcement:** Instruction-level guardrails can be overridden by a confused prompt. Script-level enforcement runs regardless of what Claude decides — the shell script is the final gate.

**Why confirmation matters:** iMessage sends are immediate and cannot be recalled. A prompt mismatch (wrong contact name, wrong number) could send a message to the wrong person.

---

### Reminders — default list, confirmation on ambiguous deletes

**Risk:** Adding reminders to the wrong list, or deleting more reminders than intended.

**Guardrails:**

- Default list is `Reminders` — new reminders go there unless a list name is explicitly stated.
- Delete operations use **case-insensitive partial matching** — if more than one reminder matches the search term, Claude lists all matches and asks you to confirm before deleting any.
- Claude will not delete all reminders in a list without explicit instruction.

---

### Contacts — read-only

**Risk:** Unintended modification or deletion of contact data.

**Guardrails:**

- **Search only** — the skill can read and return contact information but cannot add, edit, or delete any contact.
- Searches return name, phone numbers, and email — no sensitive fields (notes, addresses) unless explicitly asked.

---

### iMusic — playback control only

**Risk:** Unintended library modifications or playlist changes.

**Guardrails:**

- **Playback control only** — play, pause, skip, volume, and current track. No library edits.
- Uses AppleScript only — no API token required, no network calls.
- Playlist names must match **exactly** as they appear in Music.app (case-sensitive). Claude will not guess or fuzzy-match playlist names.
- Music.app must be open before invoking — the skill will not launch it silently.

---

### Spotify — playback control only, no URI guessing

**Risk:** Playing unintended playlists or exposing Spotify credentials.

**Guardrails:**

- **Playback control only** — play, pause, skip, volume, current track. No library modifications.
- Uses AppleScript only — no API token, no OAuth flow, no network calls to Spotify API.
- Playlists must be pre-saved in `spotify_config.py` with their Spotify URIs. Claude will **never guess or construct a URI** from a playlist name.
- Spotify must be open and signed in before invoking.

**How to add a playlist URI:** Right-click any playlist in Spotify → Share → Copy Spotify URI.

---

### SSH — host allowlist

**Risk:** Claude connecting to arbitrary or unintended remote machines.

**Guardrails (script-level, enforced in all `ssh_*.sh` tools):**

- Every tool checks the target IP/hostname against `ALLOWED_HOSTS` in `ssh_config.sh` **before connecting**. Unlisted hosts are blocked with a `BLOCKED:` message.
- The check strips the `user@` prefix — only the IP/hostname is matched. This means any user on a listed machine is allowed, but no user on an unlisted machine is ever reached.
- To disable the allowlist, set `DISABLE_HOST_RESTRICTION=true` in `ssh_config.sh` (not recommended).

**How to add a host:**

```bash
# ssh_config.sh
ALLOWED_HOSTS=(
    "dev=192.168.x.x"
    "staging=10.0.0.x"
)
```

**Why IP-only matching:** Restricting by IP/hostname (not `user@IP`) keeps the config simple — one entry covers the machine regardless of which user is needed on that box.

---

### SSH — no destructive commands without confirmation

**Risk:** Accidentally deleting data or taking down services on a remote machine.

**Guardrails (script-level, enforced in `ssh_run.sh`):**

- The following commands require **explicit user confirmation** before running:
  - `rm -rf`
  - `docker system prune`
  - `docker volume rm`
- Always connects with `BatchMode=yes` — will never hang waiting for a password prompt or interactive input.
- If the host is unreachable, the script reports the error clearly and exits — it does not retry silently.
- Uses `ControlMaster=auto` — the first call to a host creates a master socket; all subsequent calls reuse it without re-authenticating.

**Why BatchMode:** Hanging SSH sessions in a non-interactive Claude context would block the entire conversation with no clear way to recover.

**Why ControlMaster:** Reduces repeated SSH calls from ~75ms (full handshake) to ~10ms (socket reuse). Each `user@host:port` gets its own socket under `/tmp/ssh_mux_*`, so multiple remote machines are fully independent.

---

### Database queries — read-only enforcement

**Risk:** Accidentally dropping tables, altering schema, or deleting rows via a query prompt.

**Guardrails (script-level, enforced in `ssh_db_query.sh`):**

- Connects using `--read-only` MySQL flag — the server itself refuses any write operation regardless of the query content.
- Additionally, the following SQL keywords are **blocked locally before SSH connects**:
  - `DROP`, `ALTER`, `TRUNCATE`, `DELETE`, `RENAME`, `CREATE`, `REPLACE`
- Only read operations are permitted: `SELECT`, `SHOW`, `DESCRIBE`, `EXPLAIN`.
- Configure `DB_READONLY_USER` in `ssh_config.sh` to use a dedicated MySQL user with only `SELECT` grants — this is the strongest layer.

**Defence in depth:** Three layers — dedicated read-only DB user (DB_USER grants) → MySQL `--read-only` connection flag → local keyword block before SSH connects. Any one layer is sufficient; all three together make accidental writes impossible.

---

### Storage — safe cleanup rules only

**Risk:** Recommending or executing deletion of important system or app data.

**Guardrails:**

- Claude will **never recommend deleting**:
  - `~/Library/Preferences`
  - `~/Library/Application Support` (any app's data directory)
  - System files or macOS framework directories
- The Claude VM bundle (`vm_bundles/claudevm.bundle`) is reported as informational only — removal must be done through Claude app Settings, not the terminal.
- `docker system prune` is suggested as an option but never run automatically — always requires user confirmation.
- Cleanup suggestions are ranked by safety: caches and logs first, never app data or system directories.

---

### Safari — URL allowlist enforced

**Risk:** Claude navigating to arbitrary or unintended URLs, including sensitive internal tools, phishing pages, or unintended services.

**Guardrails (script-level, enforced in `safari_control.sh`):**

- `safari_control.sh open` checks every URL against the domain allowlist in `safari_config.sh` before navigating.
- If the domain is not in `ALLOWED_URLS`, the command exits with a clear blocked message — Safari is never opened.
- Matching is subdomain-aware: `github.com` also allows `gist.github.com`, `api.github.com`, etc.
- To disable the allowlist entirely, set `DISABLE_ALLOWLIST=true` in `safari_config.sh`.

**Warning on disabling:** Setting `DISABLE_ALLOWLIST=true` removes all URL restrictions — Claude can navigate Safari to any URL without limit. Only disable if you fully trust your prompts and use case.

**How to add a domain:**

```bash
# safari_config.sh
ALLOWED_URLS=(
    "google.com"
    "github.com"
    "yourdomain.com"   # add here
)
```

**Why script-level enforcement:** Instruction-level guardrails can be overridden by a confused prompt or unexpected input. Script-level enforcement runs regardless of what Claude decides — the shell script is the final gate.

---

### Remote git — user confirmation on write/destructive commands

**Risk:** Accidentally running destructive git commands on a remote repository without awareness (force push, reset, branch deletion, etc.).

**Guardrails (script-level, enforced in `ssh_git.sh`):**

- Write/destructive git subcommands (`commit`, `push`, `pull`, `merge`, `rebase`, `reset`, `checkout`, `fetch`, `add`, `rm`, `mv`, `stash pop/apply/drop/clear`, `branch -d/-D/-m`, `tag -a/-d/-f`, `clean`, `restore`, `init`, `clone`, `gc`, `prune`, `cherry-pick`, `revert`) **require explicit `y` confirmation** before SSH connects
- Confirmation prompt shows the command and remote path — user must type `y` or `Y` to proceed; anything else aborts with no SSH connection
- Repository path must be within `REMOTE_DIRS` in `ssh_config.sh` or a subdirectory of one — arbitrary paths are blocked.
- Subdirectories are automatically allowed — no need to register every nested repo individually.

**Why subdirs allowed:** Dev machines often have multiple repos under one parent directory (e.g. `/home/ubuntu/services/api`, `/home/ubuntu/services/worker`). Registering the parent once covers all of them without extra config.

---

### File transfer — directory allowlist

**Risk:** Claude copying files to or from arbitrary paths on local machine or remote, including sensitive system directories.

**Guardrails (script-level, enforced in `ssh_copy.sh` and `ssh_fetch.sh`):**

- **Local source is unrestricted** — you control your own machine and decide what to upload.
- **Remote destination and source are restricted** to `REMOTE_DIRS` in `ssh_config.sh`. Paths must be within a configured directory or use a registered nickname.
- `ssh_copy.sh` checks if the destination file already exists on remote and asks for confirmation before overwriting.
- Set `DISABLE_DIR_RESTRICTION=true` in `ssh_config.sh` to allow any remote path (not recommended).

**Why only restrict remote:** The risk is on the remote side — writing to unintended remote paths (config files, system dirs) or pulling sensitive files from unintended locations. Your local machine is your own.

---

### Network — scoped requests, no scanning

**Risk:** Claude making arbitrary HTTP requests, port scanning, or overwhelming a host with pings.

**Guardrails (script-level):**

- `network_port.sh` — validates port is 1–65535 before running; one port at a time only
- `network_curl.sh` — warns on any non-GET/HEAD method; 15s timeout; response truncated to 3000 chars to prevent context overload
- `network_ping.sh` — COUNT capped at 20 to prevent scanning
- `network_dns.sh` — only allowed record types: `A`, `AAAA`, `MX`, `TXT`, `CNAME`, `NS`, `PTR`, `SOA`
- Never run port range sweeps or multi-host scans — always one host or one port at a time

---

### Process — kill confirmation + system PID guard

**Risk:** Killing critical system processes or sending signals without user awareness.

**Guardrails (script-level, enforced in `process_kill.sh`):**

- Blocks PID < 100 — system process range, never killable
- Blocks by name: `launchd`, `kernel_task`, `WindowServer`, `loginwindow` — macOS critical processes
- Requires explicit `y` confirmation before sending any signal
- TERM is always the default — SIGKILL (`-9`) only on explicit user request

---

### Local Docker — no prune, confirmation on destructive compose

**Risk:** Bringing down running services or deleting Docker volumes/images accidentally.

**Guardrails (script-level):**

- `docker_local_compose.sh` uses an **allowlist** — only `up`, `down`, `restart`, `stop`, `ps`, `logs` are permitted. Anything else is rejected. This is intentionally an allowlist rather than a blocklist: Docker has too many destructive subcommands (`build`, `pull`, `rmi`, `system prune`, `volume rm`, etc.) to enumerate safely — a blocklist would miss new ones.
- `docker_local_compose.sh down/stop` — requires explicit `y` confirmation before running
- `docker_local_logs.sh` — no `--follow`; always a bounded snapshot (default 100 lines)
- `docker_local_stats.sh` — `--no-stream` only; never starts a live-updating stream
- `docker system prune`, `docker volume rm`, `docker rmi` are not part of this skill — handled exclusively by `docker_cleanup.sh` with its own confirmation flow

---

### Config files — read-only at OS level

**Risk:** Claude accidentally modifying skill config files (URL allowlists, SSH host mappings, playlist nicknames).

**Guardrail (OS-level, enforced by filesystem permissions):**

- All `*_config.sh` files are locked `chmod 444` (read-only for all users):
  - `safari_config.sh` — Safari URL allowlist
  - `ssh_config.sh` — SSH workstation nicknames, remote dirs, compose paths
  - `music_config.sh` — iMusic playlist nickname → Music.app name mappings
  - `spotify_config.sh` — Spotify playlist nickname → URI mappings
- Any write attempt by Claude (or any tool) fails immediately with a permission error — no instruction-level compliance required.
- To edit a config file, unlock it manually, make changes, then re-lock:

```bash
chmod 644 ~/workspace/claude_for_mac_local/<config>.sh
# edit
chmod 444 ~/workspace/claude_for_mac_local/<config>.sh
```

**Why OS-level:** Config files define the security boundaries for their respective skills (URL allowlist, allowed SSH hosts). An accidental edit by a confused prompt could silently widen or break those boundaries. Filesystem permissions are enforced by the kernel — no prompt can override them.

---

## Adding New Guardrails

When building a new skill or tool, ask:

| Question | If yes → |
| -------- | -------- |
| Can this action be irreversible? | Add confirmation before executing |
| Can this action affect data outside the intended scope? | Add a scope check (folder, calendar, domain, etc.) |
| Can this action affect a remote system? | Add a destructive-command block list |
| Is there a config-driven allowlist that makes sense? | Add one with a `DISABLE_*` escape hatch + warning |
| Can enforcement be pushed to the shell script? | Do it — script-level is stronger than instruction-level |
| Are the dangerous operations a small minority? | Use a **blocklist** (e.g. git — most subcommands are safe, block the few write ones) |
| Are the safe operations a small minority? | Use an **allowlist** (e.g. docker compose — most subcommands are destructive, permit only the few safe ones) |

The bar for adding a guardrail is: **if it is easy to implement, add it**.
