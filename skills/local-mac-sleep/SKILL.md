---
name: local-mac-sleep
description: Put the Mac to sleep — immediately, on a timer, or after a wind-down sequence (close Safari, quit all apps except VSCode, turn off Wi-Fi, then sleep). Use when the user asks to sleep the Mac, schedule sleep, cancel a scheduled sleep, or do a wind-down before sleeping.
user-invocable: true
---

Sleep controls for the local Mac. Uses `pmset` for sleep and `at` for scheduling. Wind-down closes Safari, quits all apps except VSCode, turns off Wi-Fi, then sleeps.

---

## Sleep now

```bash
~/workspace/claude_for_mac_local/tools/sleep_control.sh now
```

## Sleep in N minutes

```bash
~/workspace/claude_for_mac_local/tools/sleep_control.sh in <MINUTES>
```

Example: `sleep_control.sh in 30` — schedules sleep 30 minutes from now via `at`.

## Wind-down then sleep

```bash
~/workspace/claude_for_mac_local/tools/sleep_control.sh winddown [MINUTES]
```

- MINUTES defaults to `0` (run immediately)
- When a delay is given, the full sequence is scheduled via `at`
- Sequence: close all Safari windows → quit all apps except VSCode → turn off Wi-Fi → sleep

## Check scheduled sleep jobs

```bash
~/workspace/claude_for_mac_local/tools/sleep_control.sh status
```

## Cancel scheduled sleep

```bash
~/workspace/claude_for_mac_local/tools/sleep_control.sh cancel
```

Cancels **all** pending `at` jobs (not just sleep ones — warn the user if that matters).

---

## Guardrails

- `in` requires MINUTES ≥ 1 — rejects zero or negative values
- `winddown` keeps VSCode and Finder alive; all other GUI apps are quit gracefully via AppleScript `quit` (not force-kill)
- `cancel` removes all `at` jobs — tell the user this affects any other scheduled tasks too
- Never uses `kill -9` or force-quits system processes
