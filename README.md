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
| /apfel-vault-chat | Run private on-device chat over the full vault using apfel + MCP. |
| /kaise | Break a plain-language task into the right skills and execution order. |
| /local-mac-calendar | Read, create, and manage local Apple Calendar events. |
| /local-mac-call | Place a phone call from macOS using a contact or number. |
| /local-mac-cleanup-repo | Reset repository history and publish a fresh verified-clean state. |
| /local-mac-contacts | Find contacts and return their phone/details from macOS Contacts. |
| /local-mac-docker | Inspect and manage local Docker containers, logs, stats, and compose services. |
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
| /local-mac-spotify | Control Spotify playback, volume, and named playlists. |
| /local-mac-ssh | Connect to pre-authenticated remote workstations and run remote operations. |
| /local-mac-storage | Check disk usage and perform guided local storage cleanup. |
| /local-mac-time | Get time, set alarms, and run countdown timers with notifications. |
| /local-mac-vault | Perform unified vault read/write/search/tasks/links/session operations. |
| /local-mac-whisper | Transcribe audio/video with whisper.cpp and output text/srt files. |
| /local-mac-wifi | Toggle Wi-Fi and inspect current and nearby network status. |

Market-intel skills have been migrated out of this repository.
See `MARKET_INTEL_MIGRATION.md` for details.

## Building

**Claude - Build the swift binaries required for mcp tools**

If you want to build by yourself:

```bash
cd local-mac-mcp
bash build.sh
```

The release binary will be built to:
```
local-mac-mcp/.build/arm64-apple-macosx/release/local-mpc
```

Symlink it to the bin directory:
```bash
ln -sf local-mac-mcp/.build/arm64-apple-macosx/release/local-mpc bin/local-mcp
```

Test the build:
```bash
./bin/local-mcp --version
./bin/local-mcp call mail_list_mailboxes '{}'
```
