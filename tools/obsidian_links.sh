#!/bin/bash
# obsidian_links.sh - List outgoing links from a note via Obsidian CLI

set -euo pipefail

VAULT="claude_documents"

if [[ $# -eq 0 ]]; then
    echo "Usage: obsidian_links.sh <note_name>"
    exit 1
fi

note_name="$1"

# Remove .md extension — CLI resolves by name
note_name="${note_name%.md}"

echo "Links in '$note_name':"
echo "---"
obsidian vault="$VAULT" links file="$note_name"
