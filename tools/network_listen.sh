#!/bin/bash
# Usage: network_listen.sh
# Lists all TCP/UDP ports currently listening on this machine, with process names.

lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | awk 'NR==1 || NR>1' | sort -k9 -n
echo ""
lsof -nP -iUDP 2>/dev/null | grep -v "^COMMAND" | sort -k9 -n | head -30
