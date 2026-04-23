---
name: local-mac-sleep
description: Put the Mac to sleep — immediately, on a timer, or after a wind-down sequence (close Safari, quit all apps except VSCode, turn off Wi-Fi, then sleep). Use when the user asks to sleep the Mac, schedule sleep, cancel a scheduled sleep, or do a wind-down before sleeping.
user-invocable: true
---

Sleep controls for the local Mac via the Swift MCP binary.

---

## Sleep now

MCP tool: `sleep_now`
```json
{}
```

## Sleep in N minutes

MCP tool: `sleep_in`
```json
{ "minutes": N }
```

- N must be ≥ 1 — reject zero or negative values

## Wind-down then sleep

MCP tool: `sleep_winddown`
```json
{ "minutes": N }
```

- `minutes` defaults to `0` (run immediately)
- Sequence: close all Safari windows → quit all apps except VSCode → turn off Wi-Fi → sleep

## Check scheduled sleep status

MCP tool: `sleep_status`
```json
{}
```

## Cancel scheduled sleep

MCP tool: `sleep_cancel`
```json
{}
```

---

## Guardrails

- `sleep_in` requires minutes ≥ 1
- Wind-down keeps VSCode and Finder alive; all other GUI apps are quit gracefully
- Never force-kills system processes
