---
name: local-mac-finder
description: Open, reveal, list, create folders, and trash items via Finder. Use for file navigation on the desktop.
user-invocable: true
---

Control Finder.

## Approach
Drive Finder with `osascript` — `tell application "Finder"` supports `open`,
`reveal`, `make new folder`, and `delete` (which moves to Trash).
Use `system__spotlight_search` to locate a path first when the user names a file
rather than a path.

## Rules
- Finder's `delete` moves to Trash rather than erasing, but still confirm.
- Never operate on a path outside the user's home without saying so explicitly.
