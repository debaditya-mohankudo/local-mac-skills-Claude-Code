---
name: local-mac-notes
description: Read notes from Apple Notes app. Use when user asks to check, read, show, or list notes from a specific folder or all notes.
user-invocable: true
---

Read notes from Apple Notes using native SQLite3 access to the Envelope Index.

## How to use this skill

When invoked directly (e.g. `/local-mac-notes`), ask the user for:
1. **Action** — list notes or read a specific note (default: list)
2. **Folder** — which folder to list from (optional, default: all)
3. **Limit** — how many notes to show (default: 10)

If the user has already provided these in the same request, skip asking for what was provided.

## Listing notes

Call the `notes_list` MCP tool:
```
notes_list(limit=10, folder="")
```
- `limit` — number of recent notes to return (optional, default 20)
- `folder` — folder name to filter by (optional, empty = all folders)

Returns: JSON array with id, title, folder, created, modified, snippet

## Reading a specific note

Call the `notes_read` MCP tool:
```
notes_read(id="56836EDD-8CF8-4C55-AB77-EAA11528D1D1")
```
- `id` — the CoreData identifier from `notes_list` (required)

Returns: Full plaintext body of the note

## Listing all folders

Call the `notes_folders` MCP tool:
```
notes_folders()
```
Returns: JSON array with folder names and note counts

## Display format

**For note list:**

```
| Title | Folder | Created | Modified | Snippet |
|-------|--------|---------|----------|---------|
| Meeting notes | Work | 2026-04-10 10:30 | 2026-04-11 08:45 | Discussion of Q2 roadmap... |
| Research | Notes | 2026-04-09 14:20 | 2026-04-09 16:00 | Key findings on market trends... |
```

**For folder list:**

```
| Folder | Notes |
|--------|-------|
| Work | 5 |
| Notes | 99 |
| Msc Math | 30 |
```

- If no notes found: `No notes found.`
- If specific folder not found: List all folders and ask user to pick one

## Workflow: Read a specific note

1. Call `notes_list` to show recent notes or notes in a folder
2. User selects one by title or snippet
3. Extract the `id` from that note
4. Call `notes_read` with the `id`
5. Display the full note body
