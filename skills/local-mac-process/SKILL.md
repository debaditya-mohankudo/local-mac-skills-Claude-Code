---
name: local-mac-process
description: List running processes and kill a process by PID. Use when the user asks if a process is running or wants to stop a process.
user-invocable: true
---

Process management on the local Mac. All operations go through the **Python MCP server** (`mcp_server.py`) which calls the **Swift CLI binary** (`~/bin/local-mac-tool`). Use MCP tool use directly — `local-mpc` is retired.

> See vault: `Projects/SWIFT_CLI_MCP_MIGRATION.md`

## How to use this skill

When invoked directly (e.g. `/local-mac-process`), ask the user for:
1. **Action** — list processes or kill a process (default: list)
2. **Process name or PID** — name to search for (optional for list) or PID to kill (required for kill)

If the user has already provided these in the same request, skip asking for what was provided.

## Listing processes

MCP tool: `process_list`
```json
{ "name": "Safari" }
```

- `name` — optional process name filter (case-insensitive, returns top 30 matches)
- If name is empty, returns top 30 processes by CPU usage

Returns: JSON array with user, pid, cpu, memory, command

## Killing a process

MCP tool: `process_kill`
```json
{ "pid": 1234, "force": 0 }
```

- `pid` — the PID to kill (required, numeric string)
- `force` — 0 for SIGTERM (graceful, default), 1 for SIGKILL (force)

Returns: Confirmation message showing process name, PID, and signal sent

**Important:** Always show the user the process info and ask for confirmation before killing. Default to SIGTERM — only use SIGKILL (force=1) if the user explicitly requests it or SIGTERM didn't work.

## Display format

**For process list:**

```
| User | PID | CPU | Memory | Command |
|------|-----|-----|--------|---------|
| user | 1234 | 5.2 | 10.5 | /Applications/Safari.app/Contents/MacOS/Safari |
| user | 5678 | 2.1 | 8.3 | /Applications/Finder.app/Contents/MacOS/Finder |
```

- If no processes found: `No processes found matching "[name]".`
- If searching by name: show all matching processes (up to 30)

## Guardrails

- Blocks killing PIDs < 100 (system process range)
- Blocks critical system processes: `launchd`, `kernel_task`, `WindowServer`, `loginwindow`, `systemd`, `init`
- Always confirm with user before killing
- Default to SIGTERM (signal 15) for graceful shutdown
- Only use SIGKILL (signal 9) if user explicitly requests force kill
