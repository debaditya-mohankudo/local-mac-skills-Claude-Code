---
name: local-mac-wifi
description: Toggle Wi-Fi and inspect current and nearby networks. Use for connectivity checks and switching.
user-invocable: true
---

Control Wi-Fi.

## Script
`tools/wifi_control.sh <status|on|off|current|list>`

## Rules
- Turning Wi-Fi off may drop the session you are working in — confirm first.
- `list` shows nearby networks; it does not join them.
