---
name: local-mac-process
description: List running processes and terminate by PID. Use to find or stop a stuck process.
user-invocable: true
---

Inspect and stop processes.

## Tools and scripts
- `system__process_list` / `tools/process_list.sh [NAME]`
- `system__process_kill` / `tools/process_kill.sh PID [SIGNAL]`

## Guardrails
PIDs below 100 are refused, critical system processes are blocked, and a kill
requires explicit confirmation. Always show the process line you are about to
kill and get a yes before sending a signal.
