#!/bin/bash
# obsidian_summarize_session.sh - Append Claude session summary to daily summary note

set -euo pipefail

VAULT="claude_documents"
TODAY=$(date +%Y-%m-%d)
NOTE_PATH="Daily/${TODAY}_summary.md"

if [[ $# -eq 0 ]]; then
    echo "Usage: obsidian_summarize_session.sh \"Session summary content\""
    exit 1
fi

session_content="$1"

obsidian vault="$VAULT" append path="$NOTE_PATH" content="$session_content"

echo ""
echo "Daily Note: $TODAY"
echo "Path: $NOTE_PATH"
