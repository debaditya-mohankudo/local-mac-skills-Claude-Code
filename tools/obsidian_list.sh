#!/bin/bash
# obsidian_list.sh - List all Obsidian notes

set -euo pipefail

OBSIDIAN_DIR="$HOME/Documents/claude_documents"

if [[ ! -d "$OBSIDIAN_DIR" ]]; then
    echo "Error: Obsidian directory not found: $OBSIDIAN_DIR"
    exit 1
fi

# Count files
file_count=$(find "$OBSIDIAN_DIR" -type f -name "*.md" 2>/dev/null | wc -l)

if [[ $file_count -eq 0 ]]; then
    echo "No notes found in $OBSIDIAN_DIR"
    exit 0
fi

echo "Obsidian notes in $OBSIDIAN_DIR:"
echo "---"
find "$OBSIDIAN_DIR" -type f -name "*.md" | sed "s|$OBSIDIAN_DIR/||" | sort
