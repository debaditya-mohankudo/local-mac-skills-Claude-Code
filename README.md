# claude_for_mac_local

Full documentation lives in the Obsidian vault:

**`Documentation/Tools/WIKI_HOME.md`**

Vault path is configured in `.env` via `VAULT_PATH`.
Open in Obsidian using that path, or read via `/local-mac-vault read "Documentation/Tools/WIKI_HOME"`.

## Skills

### Quick Picks

| Skill | Use for |
|---|---|
| /local-mac-vault | Read/write/search notes in the vault quickly. |
| /local-mac-imessage | Send or read iMessages from macOS. |
| /local-mac-calendar | Add, remove, or list calendar events. |
| /local-mac-network | Check ports, DNS, ping, and endpoint health. |
| /local-mac-mail | Read recent emails from Apple Mail folders. |
| /local-mac-contacts | Search contacts and get phone details quickly. |
| /local-mac-time | Check current time, alarms, and timers. |
| /local-mac-safari | Automate Safari browsing and page interaction. |

| Skill Name | Purpose (1 sentence) |
|---|---|
| /kaise | Break a plain-language task into the right skills and execution order. |
| /local-mac-calendar | Read, create, and manage local Apple Calendar events. |
| /local-mac-call | Place a phone call from macOS using a contact or number. |
| /local-mac-cleanup-repo | Reset repository history and publish a fresh verified-clean state. |
| /local-mac-contacts | Find contacts and return their phone/details from macOS Contacts. |
| /local-mac-finder | Control Finder actions such as open, reveal, list, create folders, and trash. |
| /local-mac-imessage | Read and send iMessages through the native Messages app. |
| /local-mac-mail | Read and list emails from selected Apple Mail folders. |
| /local-mac-music | Control Music.app playback, volume, and playlist actions. |
| /local-mac-network | Check local network health, ports, DNS, ping, and endpoint reachability. |
| /local-mac-notes | Read and manage Apple Notes entries in the Claude folder. |
| /local-mac-notify | Create and review macOS Notification Center alerts. |
| /local-mac-process | List running processes and terminate by PID when needed. |
| /local-mac-reminders | Read and manage Apple Reminders with list and status filters. |
| /local-mac-safari | Automate Safari browsing, extraction, interaction, and screenshots. |
| /local-mac-scan-personal-data | Scan the repository for potential personal data before commit/push. |
| /local-mac-screencapture | Start, stop, and inspect screen recordings saved as .mov. |
| /local-mac-sleep | Sleep the Mac immediately, on timer, or via wind-down routine. |
| /local-mac-storage | Check disk usage and perform guided local storage cleanup. |
| /local-mac-time | Get time, set alarms, and run countdown timers with notifications. |
| /local-mac-vault | Perform unified vault read/write/search/tasks/links/session operations. |
| /local-mac-whisper | Transcribe audio/video with whisper.cpp and output text/srt files. |
| /local-mac-wifi | Toggle Wi-Fi and inspect current and nearby network status. |

Market-intel and astrology skills have been migrated out of this repository.

## Gates

Every `domain__action` MCP call funnels through one choke point in
`src/dispatcher.py`, which runs pre-checks from `src/tool_hooks.py` before
the call is allowed to execute. A blocked call raises `PermissionError` and
is logged (`blocked=1`) to `tool_hints.sqlite`'s `mcp_tool_calls` table
instead of running.

| Gate | Blocks | Requires |
|---|---|---|
| Vault path containment | `vault__write`, `vault__append`, `vault__delete`, `vault__move` | Resolved target path must stay inside `VAULT_PATH` — refuses any path that escapes the vault root. |
| iMessage recipient check | `imessage__send` | `contacts__search` must have run within the last 120s and found a matching contact. |
| Mail delete confirmation | `mail__delete` | `mail__read` must have run within the last 120s, so a message is read before it's deleted. |

The 120s window matches claude-hooks' `gate_rules.yaml` default and is scoped
per server process (in-memory), not per calendar time — restarting the MCP
server resets it.

## Building

If this is your first local setup, use uv to prepare Python dependencies:

```bash
# This repository is already initialized; do not run uv init here.
# Required: create/sync the virtual environment from pyproject.toml
uv sync
```

Build and install the Swift CLI binary:

```bash
cd local-mac-tool
bash build.sh
```

This builds `local-mac-tool` and installs it to `~/bin/local-mac-tool`.

The binary covers only what AppleScript cannot reach — audio output device
switching (CoreAudio) and Apple's on-device Foundation Models. Everything else
runs through AppleScript or direct SQLite reads from Python, so most tools work
without building it at all.

Test the build:
```bash
echo '{}' | ~/bin/local-mac-tool sound-get-output
```
