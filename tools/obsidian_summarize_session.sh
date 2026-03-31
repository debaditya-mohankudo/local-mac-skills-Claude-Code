#!/bin/bash
# obsidian_summarize_session.sh - Summarize Claude session and write to Daily notes

set -euo pipefail

OBSIDIAN_DIR="$HOME/Documents/claude_documents"
TODAY=$(date +%Y-%m-%d)
SESSION_FILE="$OBSIDIAN_DIR/Daily/$TODAY.md"

if [[ $# -eq 0 ]]; then
    echo "Usage: obsidian_summarize_session.sh \"Session summary content\""
    echo ""
    echo "Example:"
    echo "  obsidian_summarize_session.sh \"# Daily Session\n\nWhat we worked on...\""
    exit 1
fi

session_content="$1"

# Create Daily folder if it doesn't exist
mkdir -p "$OBSIDIAN_DIR/Daily"

# Check if file already exists
if [[ -f "$SESSION_FILE" ]]; then
    echo "ℹ️  Session note for $TODAY already exists"
    echo "Path: $SESSION_FILE"
    exit 0
fi

# Write session summary
printf '%b\n' "$session_content" > "$SESSION_FILE"

echo "✓ Session summary saved: $SESSION_FILE"
echo ""
echo "Daily Note: $TODAY"
printf '%b\n' "$session_content" | head -20
echo ""
echo "..."
