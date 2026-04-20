#!/bin/bash

# List all tasks from vault task files
VAULT_DIR="${VAULT_PATH:-$HOME/workspace/claude_documents}"
PERSONAL_TASKS="$VAULT_DIR/personal_tasks.md"
VAULT_TASKS="$VAULT_DIR/tasks.md"

echo "=== PERSONAL TASKS ==="
if [[ -f "$PERSONAL_TASKS" ]]; then
    echo ""
    grep -E "^##|^\- \[" "$PERSONAL_TASKS" | head -50
else
    echo "No personal_tasks.md found"
fi

echo ""
echo "=== VAULT TASKS ==="
if [[ -f "$VAULT_TASKS" ]]; then
    echo ""
    grep -E "^##|^\- \[" "$VAULT_TASKS" | head -50
else
    echo "No tasks.md found"
fi
