---
name: local-mac-vpn
description: Check, connect, disconnect, or temporarily pause the VPN. Use for VPN state changes.
user-invocable: true
---

Manage the VPN.

## Tools
`vpn__status` `vpn__connect` `vpn__disconnect` `vpn__pause`

## Rules
- Check `vpn__status` before and after any change and report the actual state.
- `vpn__pause` takes a duration and auto-reconnects — prefer it over a bare disconnect,
  which is easy to forget to undo.
