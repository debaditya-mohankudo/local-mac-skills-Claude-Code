---
name: local-mac-ssh
description: Connect to pre-authenticated remote workstations by user@ip or saved nickname, run remote commands, and manage Docker dev setup on the remote workstation. Use when user asks to connect to a workstation, run a command remotely, check remote Docker containers, or manage remote services.
user-invocable: true
---

Run commands on pre-authenticated remote workstations and manage Docker on them.

All machines use key-based auth — no passwords. Use `BatchMode=yes` always.

> **Config file:** `~/workspace/claude_for_mac_local/ssh_config.sh`
> Edit this file to add your workstations and set defaults.

---

## Step 1 — Read config

Always read config first:

```bash
cat ~/workspace/claude_for_mac_local/ssh_config.sh
```

Extract:
- `SSH_nickname_host` vars — known machines: nickname → `user@ip`
- `SSH_nickname_port` vars — optional non-default port per host (omitted = port 22)
- `SSH_nickname_desc` vars — human description
- `COMPOSE_PATH` — use for compose operations if no path provided
- `LOG_TAIL_LINES` — use as default for log fetches

**If a required value is `""` or the nickname is missing — ask the user. Never guess.**

---

## Step 2 — Resolve the host

- If the user provides a raw `user@ip`, use it directly (no port lookup needed unless they specify one).
- If the user provides a nickname, look up `SSH_nickname_host` (case-insensitive) for the address and `SSH_nickname_port` for the port (default 22 if not set).
- If the user says "list my workstations" or is unsure which machine to use, print the hosts table:

```
| Nickname | Host         | Port | Description         |
|----------|--------------|------|---------------------|
| dev      | ubuntu@...   | 22   | Local dev server    |
| sandbox  | testuser@... | 2222 | Docker SSH sandbox  |
```

- If the nickname is not found and no raw `user@ip` given — ask the user.

**Port handling:** When a host has a non-default port, export `SSH_PORT` before calling any script:

```bash
SSH_PORT=2222 ~/workspace/claude_for_mac_local/tools/ssh_run.sh "USER@IP" "COMMAND"
```

This applies to all `ssh_*.sh` scripts — they all inherit `SSH_PORT` from the environment.

## Saving a new host

If the user asks to add or save a new host, update `HOSTS` in the config file directly:

```bash
# Claude edits ssh_config.py to add the new entry to HOSTS
```

Confirm: `Added "NICKNAME" → USER@IP to ssh_config.py.`

---

## Running a remote command

```bash
~/workspace/claude_for_mac_local/tools/ssh_run.sh "USER@IP" "COMMAND"
```

Present output as-is. Show errors clearly.

---

## Docker operations

### List containers

```bash
~/workspace/claude_for_mac_local/tools/ssh_run.sh "USER@IP" "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
```

### Start / stop a container

```bash
~/workspace/claude_for_mac_local/tools/ssh_run.sh "USER@IP" "docker start CONTAINER_NAME"
~/workspace/claude_for_mac_local/tools/ssh_run.sh "USER@IP" "docker stop CONTAINER_NAME"
```

### View logs

Use `LOG_TAIL_LINES` from config as the default. If the user specifies a number, use that instead.

```bash
~/workspace/claude_for_mac_local/tools/ssh_run.sh "USER@IP" "docker logs --tail LOG_TAIL_LINES CONTAINER_NAME"
```

### Resource usage

```bash
~/workspace/claude_for_mac_local/tools/ssh_run.sh "USER@IP" "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'"
```

### Docker Compose — up / down / restart

Use `COMPOSE_PATH` from config. If it is `""`, ask the user for the path — do not guess.

```bash
~/workspace/claude_for_mac_local/tools/ssh_run.sh "USER@IP" "cd COMPOSE_PATH && docker compose up -d"
~/workspace/claude_for_mac_local/tools/ssh_run.sh "USER@IP" "cd COMPOSE_PATH && docker compose down"
~/workspace/claude_for_mac_local/tools/ssh_run.sh "USER@IP" "cd COMPOSE_PATH && docker compose restart SERVICE"
```

---

---

## Guardrails

- Always use `BatchMode=yes` — never prompt for passwords.
- Never guess missing config values — ask the user.
- Do not run destructive commands (`rm -rf`, `docker system prune`, `docker volume rm`) without explicit user confirmation.
- If host is unreachable: `Could not connect to USER@IP — host unreachable or SSH not responding.`
