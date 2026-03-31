---
name: local-mac-wifi
description: Control Wi-Fi on macOS — turn on/off, check status, show current network, list available networks. Use when the user asks to toggle Wi-Fi, check if Wi-Fi is on, see what network they're connected to, or list nearby networks.
user-invocable: true
---

Wi-Fi controls on the local Mac via `networksetup`. All commands run as background subprocesses — no Terminal required.

---

## Check Wi-Fi status

```bash
~/workspace/claude_for_mac_local/tools/wifi_control.sh status
```

Shows whether Wi-Fi power is On or Off.

## Turn Wi-Fi on

```bash
~/workspace/claude_for_mac_local/tools/wifi_control.sh on
```

## Turn Wi-Fi off

```bash
~/workspace/claude_for_mac_local/tools/wifi_control.sh off
```

## Show current network

```bash
~/workspace/claude_for_mac_local/tools/wifi_control.sh current
```

Shows the connected SSID and IP address. Reports "Not connected" if not associated.

## List available networks

```bash
~/workspace/claude_for_mac_local/tools/wifi_control.sh list
```

Scans for nearby Wi-Fi networks. Wi-Fi must be on. Falls back to preferred network list if `airport` binary is unavailable.

## Guardrails

- Only operates on the built-in `Wi-Fi` interface — no custom interface targeting
- `list` requires Wi-Fi to be on first; exits with a clear error if off
- Never connects to or disconnects from a specific network — status/on/off/list only
- Does not expose passwords or security keys
