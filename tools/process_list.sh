#!/bin/bash
# Usage: process_list.sh [NAME]
# Lists running processes. If NAME is given, filters by name (case-insensitive).
# Without NAME, shows top 30 by CPU usage.

NAME="$1"

if [[ -n "$NAME" ]]; then
  ps aux | head -1
  ps aux | grep -i "$NAME" | grep -v "grep" | grep -v "process_list.sh"
else
  # Top 30 by CPU
  ps aux | sort -rk 3 | head -31
fi
