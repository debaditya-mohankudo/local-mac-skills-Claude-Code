#!/bin/bash
# obsidian_delete.sh - Delete an Obsidian note

set -euo pipefail

OBSIDIAN_DIR="$HOME/Documents/claude_documents"

if [[ $# -eq 0 ]]; then
    echo "Usage: obsidian_delete.sh <note_name>"
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

# Ask for confirmation
read -p "Delete '$note_name'? (y/N): " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm "$note_path"
    echo "✓ Note deleted: $note_path"
else
    echo "Cancelled"
    exit 0
fi
