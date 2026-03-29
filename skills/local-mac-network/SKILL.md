---
name: local-mac-network
description: Check network status on the local Mac — what's on a port, curl an endpoint, ping a host, DNS lookup, list all listening ports. Use when the user asks what's using a port, whether a service is up, DNS resolution, or what ports are open.
user-invocable: true
---

Network diagnostics on the local Mac. All commands run as background subprocesses — no Terminal required.

---

## What's on a port

```bash
~/workspace/claude_for_mac_local/tools/network_port.sh PORT
```

Shows the process (name + PID) listening on TCP or UDP port.

## Curl an endpoint

```bash
~/workspace/claude_for_mac_local/tools/network_curl.sh URL [METHOD] [DATA]
```

- METHOD defaults to `GET`
- DATA is optional JSON body
- Response truncated to 3000 chars
- Always show the HTTP status code prominently

## Ping a host

```bash
~/workspace/claude_for_mac_local/tools/network_ping.sh HOST [COUNT]
```

- COUNT defaults to 4, capped at 20
- Reports reachability and average latency

## DNS lookup

```bash
~/workspace/claude_for_mac_local/tools/network_dns.sh HOST [TYPE]
```

- TYPE defaults to `A` — also supports `AAAA`, `MX`, `TXT`, `CNAME`, `NS`

## List all listening ports

```bash
~/workspace/claude_for_mac_local/tools/network_listen.sh
```

Shows all TCP/UDP ports currently listening on this machine with process names.

## Guardrails

- `network_port.sh` — validates port is 1–65535 before running
- `network_curl.sh` — warns before any non-GET/HEAD method; 15s timeout; response truncated to 3000 chars
- `network_ping.sh` — count capped at 20 to prevent scanning
- `network_dns.sh` — only allowed record types: A, AAAA, MX, TXT, CNAME, NS, PTR, SOA
- Never run port scans or range sweeps — one host or one port at a time only
