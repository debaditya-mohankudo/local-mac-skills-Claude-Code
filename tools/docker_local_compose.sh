#!/bin/bash
# Usage: docker_local_compose.sh ACTION [SERVICE] [PATH]
# Runs docker compose actions in the given PATH (defaults to current dir).
# ACTION: up, down, restart, stop, ps, logs
# Destructive actions (down, stop) require y/N confirmation.

ACTION="$1"
SERVICE="$2"
COMPOSE_PATH="${3:-.}"

# Allowlist approach: only explicitly permitted actions pass.
# Safer than a blocklist — Docker has too many destructive subcommands to enumerate
# (build, pull, rmi, system prune, volume rm, etc.). A blocklist would miss new ones.
ALLOWED_ACTIONS="up down restart stop ps logs"

if [[ -z "$ACTION" ]]; then
  echo "Usage: docker_local_compose.sh ACTION [SERVICE] [PATH]"
  echo "Actions: $ALLOWED_ACTIONS"
  exit 1
fi

if ! echo "$ALLOWED_ACTIONS" | grep -qw "$ACTION"; then
  echo "ERROR: unsupported action '$ACTION' (allowed: $ALLOWED_ACTIONS)"
  exit 1
fi

# Confirm destructive actions
if [[ "$ACTION" == "down" || "$ACTION" == "stop" ]]; then
  TARGET="${SERVICE:-all services}"
  printf "This will %s %s in %s. Continue? [y/N] " "$ACTION" "$TARGET" "$COMPOSE_PATH"
  read -r CONFIRM
  if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Aborted."
    exit 0
  fi
fi

cd "$COMPOSE_PATH" || { echo "ERROR: path not found: $COMPOSE_PATH"; exit 1; }

case "$ACTION" in
  up)
    docker compose up -d $SERVICE 2>&1
    ;;
  down)
    docker compose down $SERVICE 2>&1
    ;;
  restart)
    docker compose restart $SERVICE 2>&1
    ;;
  stop)
    docker compose stop $SERVICE 2>&1
    ;;
  ps)
    docker compose ps 2>&1
    ;;
  logs)
    docker compose logs --tail 100 $SERVICE 2>&1
    ;;
esac
