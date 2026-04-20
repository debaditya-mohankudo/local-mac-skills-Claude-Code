#!/bin/bash
# obsidian_backlinks.sh - Find backlinks to a note via Obsidian CLI

set -euo pipefail

VAULT="claude_documents"

if [[ $# -eq 0 ]]; then
    echo "Usage: obsidian_backlinks.sh <note_name>"
    exit 1
fi

note_name="$1"

# Remove .md extension — CLI resolves by name
note_name="${note_name%.md}"

echo "Backlinks to '$note_name':"
echo "---"
obsidian vault="$VAULT" backlinks file="$note_name"
