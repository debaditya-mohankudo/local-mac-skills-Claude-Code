#!/bin/bash
# obsidian_read.sh - Read an Obsidian note

set -euo pipefail

OBSIDIAN_DIR="$HOME/Documents/claude_documents"

if [[ $# -eq 0 ]]; then
    echo "Usage: obsidian_read.sh <note_name>"
    echo "Note name can be with or without .md extension"
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

cat "$note_path"
