---
name: local-mac-health-check
description: Single snapshot of battery, CPU load, memory pressure, and disk. Use for 'how is the Mac doing'.
user-invocable: true
---

One-shot system health snapshot.

## Tools
`system__battery_status` `system__cpu_status` `system__memory_status`
plus `tools/storage_overview.sh` for disk

## Output
Report as a compact table. Call out only what is actually abnormal — a health
check that flags nothing should say so in one line rather than listing every
normal reading.
