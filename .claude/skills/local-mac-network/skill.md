---
name: local-mac-network
description: Check ports, DNS, ping, HTTP endpoints, and listening sockets. Use for local network diagnosis.
user-invocable: true
---

Diagnose local network state.

## Scripts
- `tools/network_port.sh PORT` — what holds a port
- `tools/network_listen.sh` — all listening sockets
- `tools/network_dns.sh HOST [TYPE]` — DNS lookup
- `tools/network_ping.sh HOST [COUNT]` — reachability
- `tools/network_curl.sh URL [METHOD] [DATA]` — HTTP check

## Guardrails
Port range is validated, ping count is capped, DNS is allowlisted, and responses
are truncated. These limits exist so a diagnostic cannot turn into a flood — do
not work around them by calling the underlying commands directly.
