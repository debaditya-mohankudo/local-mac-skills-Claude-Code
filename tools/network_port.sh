#!/bin/bash
# Usage: network_port.sh PORT
# Shows what process is listening on a given port.

PORT="$1"

if [[ -z "$PORT" ]]; then
  echo "Usage: network_port.sh PORT"
  exit 1
fi

if ! [[ "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1 || PORT > 65535 )); then
  echo "ERROR: invalid port: $PORT (must be 1–65535)"
  exit 1
fi

RESULT=$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null)
UDP_RESULT=$(lsof -nP -iUDP:"$PORT" 2>/dev/null)

if [[ -z "$RESULT" && -z "$UDP_RESULT" ]]; then
  echo "Nothing listening on port $PORT"
  exit 0
fi

[[ -n "$RESULT" ]]     && echo "$RESULT"
[[ -n "$UDP_RESULT" ]] && echo "$UDP_RESULT"
