#!/bin/bash
# Usage: docker_local_logs.sh CONTAINER [LINES]
# Fetches the last N lines of logs from a local Docker container (no --follow).
# LINES defaults to 100.

CONTAINER="$1"
LINES="${2:-100}"

if [[ -z "$CONTAINER" ]]; then
  echo "Usage: docker_local_logs.sh CONTAINER [LINES]"
  exit 1
fi

docker logs --tail "$LINES" "$CONTAINER" 2>&1
