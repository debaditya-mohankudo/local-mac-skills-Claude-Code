---
name: local-mac-screencapture
description: Record the Mac screen to a .mov file — start, stop, check status, and list recordings. No audio. Use when the user asks to start or stop a screen recording, check if recording is active, or list saved recordings.
---

Screen recording on macOS via `screencapture -v`. No Terminal required. Recordings auto-named by date/time and saved to `~/Movies/Recordings/` by default.

## Run a screen recording command

```bash
~/workspace/claude_for_mac_local/tools/screencapture_control.sh ACTION [output_dir]
```

## Commands

```bash
# Start recording (saves to ~/Movies/Recordings/recording-YYYY-MM-DD-HH-MM-SS.mov)
~/workspace/claude_for_mac_local/tools/screencapture_control.sh start

# Start recording to a custom directory
~/workspace/claude_for_mac_local/tools/screencapture_control.sh start ~/Desktop/lectures

# Stop active recording
~/workspace/claude_for_mac_local/tools/screencapture_control.sh stop

# Check if recording is in progress
~/workspace/claude_for_mac_local/tools/screencapture_control.sh status

# List saved recordings
~/workspace/claude_for_mac_local/tools/screencapture_control.sh list
~/workspace/claude_for_mac_local/tools/screencapture_control.sh list ~/Desktop/lectures
```

## Guardrails

- Only one recording can be active at a time — starting while one is active returns an error
- Stop sends SIGINT to finalize the file cleanly before closing
- No audio captured (`-g` flag intentionally omitted)
- Output directory is created automatically if it does not exist
