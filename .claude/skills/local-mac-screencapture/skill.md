---
name: local-mac-screencapture
description: Start, stop, and inspect screen recordings saved as .mov. Use for capturing the screen.
user-invocable: true
---

Record the screen.

## Script
`tools/screencapture_control.sh` — start, stop, status, list

## Guardrails
One recording at a time; check status before starting. Stopping uses SIGINT so
the file finalises cleanly — never SIGKILL a recording, it leaves a corrupt .mov.
No audio is captured.
