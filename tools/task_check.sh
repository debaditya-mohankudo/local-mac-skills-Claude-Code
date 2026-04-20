#!/bin/bash

# Mark a task as complete
VAULT_DIR="${VAULT_PATH:-$HOME/workspace/claude_documents}"
FILE="${1}"
TASK="${2}"

if [[ -z "$FILE" ]] || [[ -z "$TASK" ]]; then
    echo "Usage: task_check.sh <file> \"task description\""
    echo "Example: task_check.sh personal_tasks.md \"Study MSC math subjects\""
    exit 1
fi

FILE_PATH="$VAULT_DIR/$FILE"

if [[ ! -f "$FILE_PATH" ]]; then
    echo "❌ File not found: $FILE"
    exit 1
fi

# Find the task with [ ] and replace with [x]
if grep -q "\[ \] $TASK" "$FILE_PATH"; then
    sed -i '' "s/\[ \] $TASK/\[x\] $TASK/" "$FILE_PATH"
    echo "✅ Task marked as complete: $TASK"
    echo ""
    grep "\[x\] $TASK" "$FILE_PATH"
elif grep -q "\[x\] $TASK" "$FILE_PATH"; then
    echo "⚠️  Task already completed: $TASK"
else
    echo "❌ Task not found: $TASK"
    echo ""
    echo "Available tasks:"
    grep "- \[" "$FILE_PATH" | head -20
    exit 1
fi
