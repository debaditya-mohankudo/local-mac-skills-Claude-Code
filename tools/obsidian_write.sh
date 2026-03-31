#!/bin/bash
# obsidian_write.sh - Write/create an Obsidian note

set -euo pipefail

OBSIDIAN_DIR="$HOME/Documents/claude_documents"

if [[ $# -lt 2 ]]; then
    echo "Usage: obsidian_write.sh <note_name> <content>"
    exit 1
fi

note_name="$1"
content="$2"

# Ensure .md extension
if [[ ! "$note_name" =~ \.md$ ]]; then
    note_name="${note_name}.md"
fi

note_path="$OBSIDIAN_DIR/$note_name"

# Create parent directories if needed
mkdir -p "$(dirname "$note_path")"

# Write content (interpret escape sequences like \n)
printf '%b\n' "$content" > "$note_path"

echo "✓ Note saved: $note_path"
