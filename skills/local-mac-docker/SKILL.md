---
name: local-mac-docker
description: Manage local Docker containers — list containers, view logs, check resource usage, and run compose commands. Use when the user asks about local Docker containers, services, or compose operations on their Mac.
user-invocable: true
---

Local Docker management on this Mac. All commands run as background subprocesses — no Terminal required.

For **remote** Docker (on a workstation), use `local-mac-ssh` instead.

---

## List containers

```bash
~/workspace/claude_for_mac_local/tools/docker_local_ps.sh
```

Shows all containers (running and stopped) with name, status, image, and ports.

## View logs

```bash
~/workspace/claude_for_mac_local/tools/docker_local_logs.sh CONTAINER [LINES]
```

- LINES defaults to 100
- No `--follow` — returns a snapshot immediately so Claude can read it

## Resource usage snapshot

```bash
~/workspace/claude_for_mac_local/tools/docker_local_stats.sh [CONTAINER]
```

- Uses `--no-stream` — one snapshot, not live
- Without CONTAINER — shows all running containers

## Compose operations

```bash
~/workspace/claude_for_mac_local/tools/docker_local_compose.sh ACTION [SERVICE] [PATH]
```

| Action | What it does |
| ------ | ------------ |
| `up` | `docker compose up -d [SERVICE]` |
| `down` | `docker compose down` — requires y/N confirmation |
| `restart` | `docker compose restart [SERVICE]` |
| `stop` | `docker compose stop [SERVICE]` — requires y/N confirmation |
| `ps` | `docker compose ps` |
| `logs` | `docker compose logs --tail 100 [SERVICE]` |

PATH defaults to current directory. Ask if unclear.

## Guardrails

- `docker_local_compose.sh down/stop` — requires explicit `y` confirmation before running
- `docker_local_logs.sh` — no `--follow`; always a bounded snapshot
- `docker_local_stats.sh` — `--no-stream` only; never a live-updating stream
- Never run `docker system prune`, `docker volume rm`, or `docker rmi` — those are handled by `docker_cleanup.sh` with its own confirmation flow
