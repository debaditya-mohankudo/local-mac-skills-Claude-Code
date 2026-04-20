#!/bin/bash
# obsidian_delete.sh - Delete an Obsidian note via Obsidian CLI

set -euo pipefail

VAULT="claude_documents"

if [[ $# -eq 0 ]]; then
    echo "Usage: obsidian_delete.sh <note_name>"
    exit 1
fi

note_name="$1"

# Remove .md extension — CLI resolves by name
note_name="${note_name%.md}"

obsidian vault="$VAULT" delete file="$note_name"

echo "✓ Note deleted: $note_name"
