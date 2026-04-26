---
name: local-mac-surfshark
description: Check Surfshark VPN status on macOS — connected/disconnected, server location, country, protocol (WireGuard/OpenVPN/IKEv2), DNS servers, and post-quantum status. Use when the user asks whether VPN is on, what server they're connected to, or anything about Surfshark status.
user-invocable: true
---

Check Surfshark VPN status on the local Mac via the native Swift tool. Reads connection state from `scutil` and server details from the Surfshark tunnel group container.

## How to use this skill

Call the `surfshark_status` MCP tool:

```
surfshark_status()
```

No arguments required.

## What it returns

| Field | Description |
|-------|-------------|
| `connected` | `true` / `false` — is VPN active |
| `connections` | Array of all Surfshark VPN configurations, each with `name`, `state`, `protocol` |
| `server` | Location name (e.g. "Frankfurt #1") — only when connected |
| `country_code` | ISO country code (e.g. "DE") — only when connected |
| `server_address` | VPN server hostname/IP — only when connected |
| `vpn_protocol` | e.g. `"WireGuard"`, `"OpenVPN"`, `"IKEv2"` — only when connected |
| `transport` | Transport layer (e.g. `"UDP"`) — only when connected |
| `post_quantum` | `true` / `false` — post-quantum encryption active — only when connected |
| `ip_address` | Assigned tunnel IP — only when connected |
| `dns_servers` | Array of DNS server IPs in use — only when connected |
| `interface` | Network interface name (e.g. `"utun5"`) — only when connected |

## Display format

**When connected:**

```
VPN: Connected
Server:       Frankfurt #1 (DE)
Protocol:     WireGuard / UDP
Post-quantum: Yes
Tunnel IP:    10.x.x.x
DNS:          100.64.x.x
Interface:    utun5
```

**When disconnected:**

```
VPN: Disconnected
Configurations: Surfshark WireGuard, Surfshark IKEv2
```

- If `connections` is empty: "No Surfshark VPN configurations found."
- Never expose the server address or DNS IPs unless the user explicitly asks for them
