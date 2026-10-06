---
name: local-mac-notes
description: Read and manage Apple Notes. Use for listing, reading, adding, editing, or deleting notes.
user-invocable: true
---

Work with Apple Notes.

## Tools
`notes__list` `notes__read` `notes__folders` `notes__add` `notes__update` `notes__delete`

## Rules
- Edit with `notes__update` (by id) instead of delete-and-recreate: `mode="replace"` swaps the content below the title (the title is kept unless `title` is given), `mode="append"` adds to the end. Bodies are HTML, as in `notes__add`. A password-locked note cannot be edited.
- Confirm before `notes__delete`.
- For anything that belongs in the knowledge base, prefer the vault skill — Notes is for Apple-native captures.
