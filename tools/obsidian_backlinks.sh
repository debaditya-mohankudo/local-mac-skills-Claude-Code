#!/bin/bash
# obsidian_backlinks.sh - Find backlinks to a note (notes that reference it)

set -euo pipefail

OBSIDIAN_DIR="$HOME/Documents/claude_documents"

if [[ $# -eq 0 ]]; then
    echo "Usage: obsidian_backlinks.sh <note_name>"
    exit 1
fi

note_name="$1"

# Remove .md extension for pattern matching
note_base="${note_name%.md}"

if [[ ! -d "$OBSIDIAN_DIR" ]]; then
    echo "Error: Obsidian directory not found: $OBSIDIAN_DIR"
    exit 1
fi

echo "Backlinks to '$note_base':"
echo "---"

# Search for bidirectional links [[note_base]] in all markdown files
found=0
while IFS= read -r file; do
    if grep -q "\[\[$note_base\]\]" "$file" 2>/dev/null; then
        echo "$(basename "$file")"
        found=$((found + 1))
    fi
done < <(find "$OBSIDIAN_DIR" -type f -name "*.md")

if [[ $found -eq 0 ]]; then
    echo "No backlinks found"
fi
