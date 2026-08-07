#!/bin/bash
# Usage: network_ping.sh HOST [COUNT]
# Pings a host N times (default: 4) and reports reachability + avg latency.

HOST="$1"
COUNT="${2:-4}"

if [[ -z "$HOST" ]]; then
  echo "Usage: network_ping.sh HOST [COUNT]"
  exit 1
fi

# Block scanning-style counts
if (( COUNT > 20 )); then
  echo "ERROR: count capped at 20 to prevent scanning"
  exit 1
fi

ping -c "$COUNT" -t 10 "$HOST" 2>&1
