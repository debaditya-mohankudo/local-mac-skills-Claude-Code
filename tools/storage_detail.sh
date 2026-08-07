#!/bin/bash
# Usage: storage_detail.sh
# Detailed breakdown of Library subdirs, Application Support, Caches, and Containers.
echo "=== Library Subdirectories (top 15) ==="
du -sh ~/Library/* 2>/dev/null | sort -rh | head -15

echo ""
echo "=== Application Support (top 20) ==="
find "$HOME/Library/Application Support" -maxdepth 1 -type d -exec du -sh {} \; 2>/dev/null | sort -rh | head -20

echo ""
echo "=== Caches (top 15) ==="
du -sh ~/Library/Caches/* 2>/dev/null | sort -rh | head -15

echo ""
echo "=== Containers (top 10) ==="
du -sh ~/Library/Containers/* 2>/dev/null | sort -rh | head -10
