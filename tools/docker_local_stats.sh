#!/bin/bash
# Usage: docker_local_stats.sh [CONTAINER]
# Snapshot of CPU/memory usage for all containers (or one specific container).
# Uses --no-stream so it returns immediately instead of live-updating.

CONTAINER="$1"

if [[ -n "$CONTAINER" ]]; then
  docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}' "$CONTAINER" 2>&1
else
  docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}' 2>&1
fi
