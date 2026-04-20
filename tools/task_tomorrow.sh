#!/bin/bash

# Show tomorrow's tasks for a given date
DATE="${1:-2026-04-01}"
VAULT_DIR="${VAULT_PATH:-$HOME/workspace/claude_documents}"
PERSONAL_TASKS="$VAULT_DIR/personal_tasks.md"

if [[ ! -f "$PERSONAL_TASKS" ]]; then
    echo "❌ personal_tasks.md not found"
    exit 1
fi

echo "=== Tomorrow ($DATE) Tasks ==="
echo ""

# Extract the Tomorrow section for the given date
awk -v date="## Tomorrow ($DATE)" '
    $0 ~ date { found=1; next }
    found && /^## / && !/## Tomorrow/ { exit }
    found { print }
' "$PERSONAL_TASKS"
