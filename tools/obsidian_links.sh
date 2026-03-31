#!/bin/bash
# obsidian_links.sh - Extract all links from a note

set -euo pipefail

OBSIDIAN_DIR="$HOME/Documents/claude_documents"

if [[ $# -eq 0 ]]; then
    echo "Usage: obsidian_links.sh <note_name>"
    exit 1
fi

note_name="$1"

# Ensure .md extension
if [[ ! "$note_name" =~ \.md$ ]]; then
    note_name="${note_name}.md"
fi

note_path="$OBSIDIAN_DIR/$note_name"

if [[ ! -f "$note_path" ]]; then
    echo "Error: Note not found at $note_path"
    exit 1
fi

echo "Links in '$(basename "$note_name")':"
echo "---"

# Extract all [[link]] patterns
result=$(grep -o '\[\[[^]]*\]\]' "$note_path" 2>/dev/null | sed 's/\[\[//;s/\]\]//' | sort -u)
if [[ -z "$result" ]]; then
    echo "No links found"
else
    echo "$result"
fi
