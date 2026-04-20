#!/bin/bash
# obsidian_write.sh - Write/create an Obsidian note via Obsidian CLI

set -euo pipefail

VAULT="claude_documents"

if [[ $# -lt 2 ]]; then
    echo "Usage: obsidian_write.sh <note_name> <content>"
    exit 1
fi

note_name="$1"
content="$2"

# Ensure .md extension for path targeting
if [[ ! "$note_name" =~ \.md$ ]]; then
    note_name="${note_name}.md"
fi

obsidian vault="$VAULT" create path="$note_name" content="$content" overwrite

echo "✓ Note saved: $note_name"
