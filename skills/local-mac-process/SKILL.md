---
name: local-mac-process
description: List running processes, find what's on a port, and kill a process by PID. Use when the user asks if a process is running, what's using a port, or wants to stop a process.
user-invocable: true
---

Process management on the local Mac. All commands run as background subprocesses — no Terminal required.

---

## List processes

```bash
~/workspace/claude_for_mac_local/tools/process_list.sh [NAME]
```

- With NAME — filters by process name (case-insensitive)
- Without NAME — shows top 30 processes by CPU usage

## What's on a port

```bash
~/workspace/claude_for_mac_local/tools/network_port.sh PORT
```

Use `network_port.sh` from `local-mac-network` — it covers port lookup.

## Kill a process

```bash
~/workspace/claude_for_mac_local/tools/process_kill.sh PID [SIGNAL]
```

- SIGNAL defaults to `TERM` (graceful shutdown)
- Use `SIGNAL=9` only if TERM didn't work and user explicitly asks for force kill
- Always show the process info and ask y/N before killing
- Never kill without confirmation — sends are immediate and may lose data

## Guardrails

- `process_kill.sh` — blocks PID < 100 (system process range)
- `process_kill.sh` — blocks critical process names: `launchd`, `kernel_task`, `WindowServer`, `loginwindow`
- `process_kill.sh` — requires explicit `y` confirmation before sending signal
- Never suggest `kill -9` as the first option — always try TERM first
