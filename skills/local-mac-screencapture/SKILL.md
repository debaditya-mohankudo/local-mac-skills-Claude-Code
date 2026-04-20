---
name: local-mac-screencapture
description: Record the Mac screen to a .mov file — start, stop, check status, and list recordings. No audio. Use when the user asks to start or stop a screen recording, check if recording is active, or list saved recordings.
user-invocable: true
---

Screen recording on macOS. Recordings saved to `~/Movies/Recordings/` by default, auto-named by date/time. No audio captured.

> **ScreenTool was dropped** in the Swift → Python MCP migration (2026-04-18). Uses shell script directly: `tools/screencapture_control.sh`. See vault: `Projects/SWIFT_CLI_MCP_MIGRATION.md`

## How to use this skill

When invoked directly (e.g. `/local-mac-screencapture`), ask the user for:
1. **Action** — start, stop, status, or list (default: status)
2. **Output directory** — custom save location (optional, default: `~/Movies/Recordings/`)

If the user has already provided these in the same request, skip asking for what was provided.

## Starting a recording

```bash
~/workspace/claude_for_mac_local/tools/screencapture_control.sh start [output_dir]
```

- `output_dir` — optional custom save directory (default: `~/Movies/Recordings/`)
- Returns: Success message with recording status

## Stopping a recording

```bash
~/workspace/claude_for_mac_local/tools/screencapture_control.sh stop
```

- Sends SIGINT to finalize the .mov file cleanly
- Returns: Confirmation of stopped recording and file path

## Checking recording status

```bash
~/workspace/claude_for_mac_local/tools/screencapture_control.sh status
```

- Returns: Current recording status (active or idle, file path if recording)

## Listing recordings

```bash
~/workspace/claude_for_mac_local/tools/screencapture_control.sh list [output_dir]
```

- Returns: List of recordings with filename and size

## Display format

**For recording list:**

```
| Filename | Size |
|----------|------|
| recording-2026-04-11-14-30-45.mov | 125 MB |
| recording-2026-04-11-15-02-18.mov | 89 MB |
```

- If no recordings found: `No recordings found in [directory].`

## Guardrails

- Only one recording can be active at a time — starting while one is active returns an error
- Stop sends SIGINT to finalize the file cleanly before closing
- No audio captured (intentional)
- Output directory is created automatically if it does not exist
