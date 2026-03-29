#!/bin/bash
# Usage: ssh_run.sh USER@IP "COMMAND"
# Runs a command on a remote host via SSH (pre-authenticated, no password).

HOST="$1"
COMMAND="$2"

if [[ -z "$HOST" || -z "$COMMAND" ]]; then
  echo "Usage: ssh_run.sh USER@IP \"COMMAND\""
  exit 1
fi

source "$(dirname "$0")/ssh_common.sh"

CONFIG="$HOME/workspace/claude_for_mac_local/ssh_config.sh"
[[ -f "$CONFIG" ]] && source "$CONFIG"
check_allowed_host "$HOST" || exit 1

ssh "${SSH_OPTS[@]}" "$HOST" "$COMMAND"
