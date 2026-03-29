#!/bin/bash
# Mac Storage Cleanup — Safe to Run
# Generated: 2026-03-21
# Run: chmod +x safe_to_del.sh && ./safe_to_del.sh

echo "=== Mac Storage Cleanup ==="
df -h / | tail -1

echo ""
echo "--- Pip cache ---"
pip3 cache purge

echo ""
echo "--- Homebrew cache ---"
brew cleanup

echo ""
echo "--- Browser & app caches ---"
rm -rf ~/Library/Caches/Microsoft\ Edge
rm -rf ~/Library/Caches/Mozilla
rm -rf ~/Library/Caches/Firefox
rm -rf ~/Library/Caches/Zoho
rm -rf ~/Library/Caches/us.zoom.xos
rm -rf ~/Library/Caches/ru.keepcoder.Telegram
echo "Done."

echo ""
echo "--- Playwright cache ---"
rm -rf ~/Library/Caches/ms-playwright
echo "Done."

echo ""
echo "--- Docker (ALL unused images/containers) ---"
echo "WARNING: This removes all Docker images not attached to a running container."
read -p "Proceed with docker system prune -a? (y/N) " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
    docker system prune -a -f
else
    echo "Skipped."
fi

echo ""
echo "=== Cleanup complete. Disk status: ==="
df -h /

echo ""
echo "NOTE: Claude VM bundle (11 GB) — remove via Claude app Settings → clear local model data."
