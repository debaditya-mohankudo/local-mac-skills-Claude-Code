---
name: local-mac-notify
description: Post a macOS notification. Use to signal completion of a long-running task.
user-invocable: true
---

Send a macOS notification.

## Tools
- `system__notify` — title and message to Notification Center

## Rules
- Keep it to one line; a notification is a signal, not a report.
- Use for genuine completion or a state change worth interrupting for, not routine progress.
