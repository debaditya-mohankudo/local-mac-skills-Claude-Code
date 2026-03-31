---
name: claude-mac-obsidian
description: Read and write Obsidian markdown notes with bidirectional links [[reference]]. Create, update, delete, and analyze notes in ~/Documents/claude_documents.
user-invocable: true
---

Manage Obsidian notes with full support for:
- **Bidirectional links** — `[[note-name]]` syntax for cross-referencing
- **Markdown formatting** — full Markdown support
- **Note organization** — folder hierarchies (e.g., `Projects/My Project`)
- **Link analysis** — find forward links and backlinks
- **Obsidian vault** — all notes stored in `~/Documents/claude_documents` (Obsidian-compatible)

**Step 1 — Determine the operation:**

Detect intent from the user's message:
- **read** — "show me", "read", "open", "display note"
- **write** — "save", "create", "write", "update", "add note"
- **list** — "show all", "list notes", "what notes"
- **delete** — "delete note", "remove note"
- **links** — "what links", "find links", "show references"
- **backlinks** — "what references", "backlinks", "who links to"

Branch to the appropriate section below.

---

## READ operation

**Step 2a — Extract note name:**

From the user's message, extract the note name (with or without `.md` extension).

**Step 3a — Read the note:**

```bash
~/workspace/claude_for_mac_local/tools/obsidian_read.sh "Note Name"
```

**Step 4a — Display:**

Show the full markdown content of the note, preserving all formatting and links.

---

## WRITE operation

**Step 2b — Extract note details:**

From the user's message extract:
- **note name** (required) — the note title (can include folder paths: `Projects/My Project`)
- **content** (required) — the markdown content

**Step 3b — Create/update the note:**

```bash
~/workspace/claude_for_mac_local/tools/obsidian_write.sh "Note Name" "# Heading\n\nContent with [[links]]"
```

**Step 4b — Confirm:**

Output: `✓ Note saved: ~/Documents/claude_documents/Note Name.md`

**Tips:**
- Use `\n` for newlines in the content
- Bidirectional links use double brackets: `[[Other Note]]`
- Folder paths are supported: `Projects/My Project` → `Projects/My Project.md`

---

## LIST operation

**Step 2c — List all notes:**

```bash
~/workspace/claude_for_mac_local/tools/obsidian_list.sh
```

**Step 3c — Display:**

Show all notes found in `~/Documents/claude_documents`, including folder paths, sorted alphabetically.

---

## DELETE operation

**Step 2d — Extract note name:**

From the user's message, extract the note name to delete.

**Step 3d — Delete the note:**

```bash
~/workspace/claude_for_mac_local/tools/obsidian_delete.sh "Note Name"
```

The script will ask for confirmation. Show the confirmation prompt to the user if running interactively.

**Step 4d — Confirm:**

Output the result of the deletion.

---

## LINKS operation

**Step 2e — Extract note name:**

From the user's message, extract the note name to analyze.

**Step 3e — Extract forward links:**

```bash
~/workspace/claude_for_mac_local/tools/obsidian_links.sh "Note Name"
```

**Step 4e — Display:**

Show all `[[bidirectional-links]]` found in the note, listed one per line and sorted alphabetically.

---

## BACKLINKS operation

**Step 2f — Extract note name:**

From the user's message, extract the note name to find backlinks for.

**Step 3f — Find backlinks:**

```bash
~/workspace/claude_for_mac_local/tools/obsidian_backlinks.sh "Note Name"
```

**Step 4f — Display:**

Show all notes that reference the given note via `[[note-name]]` links.

---

## Notes

- **File paths** — use note names without `.md` (automatically added)
- **Folder support** — use folder paths: `Projects/My Project` becomes `Projects/My Project.md`
- **Location** — all notes saved to `~/Documents/claude_documents`
- **Obsidian compatibility** — folder is ready to open as Obsidian vault
- **Link format** — bidirectional links use `[[Note Name]]` (case-sensitive)
