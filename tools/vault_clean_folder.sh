#!/usr/bin/env bash
# vault_clean_folder.sh — Delete all notes in a vault folder via Obsidian CLI
#
# Usage:
#   vault_clean_folder.sh [folder] [vault]
#
# Defaults:
#   folder = Tmp
#   vault  = claude_documents
#
# Exits 0 whether or not any files were found.

FOLDER="${1:-Tmp}"
VAULT="${2:-claude_documents}"

files=$(obsidian vault="$VAULT" files folder="$FOLDER" 2>/dev/null)

if [[ -z "$files" ]]; then
  exit 0
fi

while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  obsidian vault="$VAULT" delete file="$FOLDER/$f"
done <<< "$files"
