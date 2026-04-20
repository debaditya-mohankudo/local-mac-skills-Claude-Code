#!/bin/bash
# obsidian_list.sh - List all Obsidian notes via Obsidian CLI

set -euo pipefail

VAULT="claude_documents"

echo "Obsidian notes in vault '$VAULT':"
echo "---"
obsidian vault="$VAULT" files ext=md
