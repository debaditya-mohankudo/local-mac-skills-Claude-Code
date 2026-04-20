#!/bin/bash
# obsidian_read.sh - Read an Obsidian note via Obsidian CLI

set -euo pipefail

VAULT="claude_documents"

if [[ $# -eq 0 ]]; then
    echo "Usage: obsidian_read.sh <note_name>"
    echo "Note name can be with or without .md extension"
    exit 1
fi

note_name="$1"

# Remove .md extension — CLI resolves by name
note_name="${note_name%.md}"

obsidian vault="$VAULT" read file="$note_name"
