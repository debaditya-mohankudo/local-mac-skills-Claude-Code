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
| /market-intel-live-news | Get the latest RSS news digest with categories. |
| /market-intel-live-prices | Fetch live prices for the 9 tracked tickers. |
| /market-intel-morning-brief | Run the full start-of-day market snapshot. |
| /market-intel-portfolio-check | Review allocation, triggers, and risk constraints. |

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
| /market-intel-ceasefire-reached | Check which ceasefire signals fired and the current risk level. |
| /market-intel-evening-adr | Fetch and summarize Indian ADR moves during the evening window. |
| /market-intel-evening-brief | Generate a full evening brief across ADR, flows, and Nifty context. |
| /market-intel-fii-dii-check | Report daily FII/DII flows with streak and monthly totals. |
| /market-intel-gold | Classify gold regime and recommend BUY/HOLD/TRIM-style action. |
| /market-intel-live-news | Build a live RSS-based geopolitical + market news digest. |
| /market-intel-live-prices | Fetch real-time prices for the 9 monitored core tickers. |
| /market-intel-market-refresh | Refresh cached market data and append latest live quote snapshot. |
| /market-intel-morning-brief | Produce the full morning market-intel starter brief. |
| /market-intel-nifty-analysis | Analyze Nifty price action with flows, VIX, and expiry context. |
| /market-intel-portfolio-check | Show allocation, triggers, dry powder, and portfolio constraints. |
| /market-intel-query | Run historical regime-aware query analysis for custom market conditions. |
| /market-intel-watchlist-check | Check live watchlist prices versus entry zones and patch watchlist wiki prices. |

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
