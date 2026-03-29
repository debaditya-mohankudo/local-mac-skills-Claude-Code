#!/bin/bash
# Usage: docker_local_ps.sh
# Lists all local Docker containers (running and stopped).

docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}' 2>&1
