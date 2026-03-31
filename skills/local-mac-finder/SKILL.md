---
name: local-mac-finder
description: Control macOS Finder — open folders/files, reveal items, list windows, get selected paths, create folders, move to Trash. Use when the user asks to navigate to a folder, show a file in Finder, reveal a file's location, list open Finder windows, get selected files, create a new folder, or move something to Trash.
user-invocable: true
---

Control macOS Finder via AppleScript. No extra setup required — Finder is always running.

---

## Read state

```bash
~/workspace/claude_for_mac_local/tools/finder_read.sh front-path   # path of the front Finder window
~/workspace/claude_for_mac_local/tools/finder_read.sh list-windows  # all open windows and their paths
~/workspace/claude_for_mac_local/tools/finder_read.sh selection     # POSIX paths of selected items
~/workspace/claude_for_mac_local/tools/finder_read.sh list-apps     # list all running GUI apps
```

## Open / reveal

```bash
~/workspace/claude_for_mac_local/tools/finder_control.sh open PATH    # open a folder or file in Finder
~/workspace/claude_for_mac_local/tools/finder_control.sh reveal PATH  # select an item in its parent folder
```

## Create folder

```bash
~/workspace/claude_for_mac_local/tools/finder_control.sh mkdir PATH   # create folder and reveal it in Finder
```

Restricted to paths within `$HOME` — system directories are blocked.

## Move to Trash

```bash
~/workspace/claude_for_mac_local/tools/finder_control.sh trash PATH   # move to Trash (prompts y/N)
```

Always confirms with the user before trashing. The item goes to `~/.Trash` and is recoverable.

## Quit all apps (except VSCode)

```bash
~/workspace/claude_for_mac_local/tools/finder_control.sh quit-apps
```

Lists all running GUI apps then quits them one by one with a 1s gap. Keeps VSCode (Code) and Finder alive.

## Guardrails

- `open` and `reveal` validate that the path exists before calling AppleScript.
- `mkdir` is restricted to `$HOME` subtree — will not create directories in system paths.
- `trash` requires explicit `y/N` confirmation — never moves files without user approval.
- If AppleScript errors with "application isn't running", Finder is always running on macOS — check if the path is valid.
- Never delete permanently — always use `trash`, not `rm`.
