# Future Skills

Candidate skills to build next. All are feasible with `osascript` + bash on macOS.

**Last updated:** 2026-03-22

---

## Done ✓

| Skill | What it does |
| ----- | ------------ |
| ~~`local-mac-safari`~~ | Browse, scrape, automate Safari — AppleScript + JS execution |
| ~~`local-mac-ssh`~~ | Run commands and manage Docker on remote workstations |
| ~~`local-mac-imessage`~~ | Send and read iMessages via AppleScript + chat.db |
| ~~`local-mac-mail`~~ | Read emails from macOS Mail app |
| ~~`local-mac-calendar`~~ | List, add, delete Apple Calendar events |
| ~~`local-mac-notes`~~ | Read, add, delete Apple Notes (Claude folder) |
| ~~`local-mac-reminders`~~ | Read, add, delete Apple Reminders |
| ~~`local-mac-contacts`~~ | Search Contacts by name |
| ~~`local-mac-storage`~~ | Disk usage analysis and cleanup recommendations |
| ~~`local-mac-music`~~ | Control iMusic — play/pause/skip/volume/list playlists |
| ~~`local-mac-spotify`~~ | Control Spotify — play/pause/skip/volume via AppleScript |
| ~~`local-mac-finder`~~ | Open folders, reveal files, list windows, mkdir, trash |

---

## Shell skills — dev environment

Frequently used shell commands wrapped as skills. All run as background subprocesses — no Terminal.app required.

| Skill | What it does |
| ----- | ------------ |
| ~~`local-mac-network`~~ | ~~Port lookup (`lsof -i :PORT`), curl endpoint health check, ping, DNS lookup, list all listening ports~~ — done ✓ |
| ~~`local-mac-process`~~ | ~~List processes by name, find what's on a port, kill a process (y/N confirmation, system PID guard)~~ — done ✓ |
| ~~`local-mac-docker`~~ | ~~Local Docker — `ps -a`, logs (no follow), stats snapshot, compose up/down/restart~~ — done ✓ |

---

## High value — straightforward

| App | What you'd get |
| --- | -------------- |
| ~~**Finder**~~ | ~~Open folders, move/copy/rename files, reveal in Finder, trash items~~ — done ✓ |
| ~~**Safari**~~ | ~~Open URL, get current tab title/URL, list open tabs, search bookmarks~~ — done ✓ |
| **Apple Shortcuts** | Run any existing Shortcut by name — multiplier since Shortcuts can do almost anything |
| **Voice Memos** | List recordings, play by name |
| ~~**`local-mac-wifi`**~~ | ~~Wi-Fi on/off, status, current SSID, list available networks — via `networksetup`~~ — done ✓ |
| ~~**`local-mac-screencapture`**~~ | ~~Screen recording via `screencapture -v` — start, stop, status, list. No audio.~~ — done ✓ |
| **System Settings toggles** | Bluetooth on/off, Dark Mode toggle, Do Not Disturb — via `osascript` |
| **Clipboard** | Read current clipboard (`pbpaste`), write to it (`pbcopy`) — pipe Claude output into other apps |
| **Screenshot** | Capture screen/window/selection via `screencapture` |

---

## Under consideration — responsibility overlap

These skills have partial overlap with existing skills. Build only after the responsibility boundary is clear.

| Skill | What it would do | Overlap / open question |
| ----- | ---------------- | ----------------------- |
| **`local-mac-terminal`** | Open Terminal windows/tabs, run commands, SSH into remotes with live output (e.g. `docker logs --follow`) | **No overlap with `local-mac-ssh`** — ssh skill runs as a background subprocess and never opens Terminal.app. Terminal skill is only useful for live streaming (`--follow`, interactive sessions) — roughly 5% of DevOps use cases. `ssh_logs.sh` already covers most "what's happening" questions without a live stream. **Low priority.** |

→ See [EXECUTION_MODEL_WIKI.md](EXECUTION_MODEL_WIKI.md) for the full performance comparison and execution model breakdown.

---

## Slightly more involved but useful

| App | Notes |
| --- | ----- |
| **Activity Monitor** | Top CPU/memory processes — doable with `ps`/`top`, needs a skill wrapper |
| **App launcher** | Open/quit/list running apps — pure AppleScript, no permissions needed |
| **Notification Center** | Send a local notification — one-liner with `osascript` |
| **Slack** | Send messages to channels via Incoming Webhooks (`curl`); bot token variant for DMs |
| **FaceTime / Phone** | Initiate calls via `tel://` URL scheme + `open` command |
| **Maps** | Open directions to an address — via URL scheme |

---

## Priority order

1. **Apple Shortcuts** — lets Claude trigger anything already built in Shortcuts
2. **System toggles** — Wi-Fi, Bluetooth, Dark Mode are asked constantly
3. **Slack** — send messages to channels/DMs, one `curl` call with a webhook
4. **Clipboard** — simple but very high utility for piping Claude output into other apps
5. **Screenshot** — capture + describe, useful for debugging UI issues
