#!/bin/bash
# Usage: storage_overview.sh
# Shows disk usage overview and top-level home directory sizes.
echo "=== Disk Usage ==="
df -h /

echo ""
echo "=== Home Directory ==="
du -sh ~/Library ~/Downloads ~/Desktop ~/Documents ~/.Trash 2>/dev/null | sort -rh
