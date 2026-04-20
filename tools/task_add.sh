#!/bin/bash

# Add a new task to personal_tasks.md
VAULT_DIR="${VAULT_PATH:-$HOME/workspace/claude_documents}"
PERSONAL_TASKS="$VAULT_DIR/personal_tasks.md"

SECTION="${1}"
PRIORITY="${2}"
TASK="${3}"

if [[ -z "$SECTION" ]] || [[ -z "$PRIORITY" ]] || [[ -z "$TASK" ]]; then
    echo "Usage: task_add.sh \"Section\" \"Priority 1|2|3\" \"[ ] Task description\""
    echo "Example: task_add.sh \"Tomorrow (2026-04-01)\" \"Priority 1\" \"[ ] Study math\""
    exit 1
fi

if [[ ! -f "$PERSONAL_TASKS" ]]; then
    echo "❌ personal_tasks.md not found at $PERSONAL_TASKS"
    exit 1
fi

# Check if section exists
if ! grep -q "^## $SECTION" "$PERSONAL_TASKS"; then
    echo "❌ Section \"$SECTION\" not found"
    echo "Available sections:"
    grep "^## " "$PERSONAL_TASKS" | sed 's/^## //'
    exit 1
fi

# Find the line number of the section
SECTION_LINE=$(grep -n "^## $SECTION" "$PERSONAL_TASKS" | cut -d: -f1)

# Find the next section or end of file
NEXT_SECTION_LINE=$(tail -n +$((SECTION_LINE + 1)) "$PERSONAL_TASKS" | grep -n "^## " | head -1 | cut -d: -f1)

if [[ -z "$NEXT_SECTION_LINE" ]]; then
    # Add at end of file
    echo "$TASK" >> "$PERSONAL_TASKS"
    echo "✅ Task added to end of \"$SECTION\""
else
    # Insert before next section
    INSERT_LINE=$((SECTION_LINE + NEXT_SECTION_LINE - 1))
    sed -i '' "${INSERT_LINE}i\\
$TASK
" "$PERSONAL_TASKS"
    echo "✅ Task added to \"$SECTION\""
fi

# Show updated section
echo ""
awk -v section="## $SECTION" '
    $0 ~ section { found=1; print; next }
    found && /^## / && !/section/ { exit }
    found { print }
' "$PERSONAL_TASKS"
