---
name: local-mac-notes
description: Use this skill when the user asks to read, list, add, create, delete, or remove Apple Notes. Restricted to the "Claude" folder only.
user-invocable: true
---

Read, add, or delete Apple Notes via AppleScript. All operations are restricted to the **"Claude"** folder.

> Note: If you get a "folder not found" error, the folder may be named "Claud" (typo). Rename it in Notes.app → Folders sidebar, then retry.

**Step 1 — Determine the operation:**

Detect intent from the user's message:
- **list** — show/list/read notes (default)
- **add** — "add note", "create note", "save this as a note", "note this down"
- **delete** — "delete note", "remove note"

Branch to the appropriate section below.

---

## ADD operation

**Step 2a — Extract note details:**

From the user's message extract:
- **title** (required) — first line / explicit title
- **body** — the note content (everything after the title, or the full text if no title is given)

If no explicit title, use the first sentence of the body as the title.

**Step 3a — Create the note:**

```bash
~/workspace/claude_for_mac_local/tools/notes_add.sh "TITLE" "BODY"
```

**Step 4a — Confirm:**

Output: `Added note "[title]" to Claude folder.`

---

## DELETE operation

**Step 2b — Identify what to delete:**

Extract the note title or partial name from the user's message.

**Step 3b — Find the note:**

```bash
~/workspace/claude_for_mac_local/tools/notes_list.sh
```

Find notes whose name contains the search string (case-insensitive). If multiple matches, list them and ask the user to confirm which one. If exactly one match, proceed.

**Step 4b — Delete the note:**

```bash
~/workspace/claude_for_mac_local/tools/notes_delete.sh "EXACT TITLE"
```

**Step 5b — Confirm:**

Output: `Deleted note "[title]" from Claude folder.`

---

## LIST operation

**Step 2c — Parse list filters:**

- No qualifier → list all notes (titles + date modified + body preview)
- `search [keyword]` → filter notes whose title or body contains keyword
- `show [title]` → show full body of a specific note

**Step 3c — Fetch notes:**

```bash
~/workspace/claude_for_mac_local/tools/notes_list.sh
```

For `show [title]`, fetch the full body:

```bash
~/workspace/claude_for_mac_local/tools/notes_read.sh "TITLE"
```

**Step 4c — Display:**

```
## Notes — Claude folder — [DATE]

### [Title]
*Modified: Mon, 21 Mar 2026*
[body preview or full body]

---

**Total: X note(s)**
```

Rules:
- Show body preview (first 120 chars) for list view; full body for `show` command
- If folder is empty: `No notes found in Claude folder.`
- If search returns no matches: `No notes matching "[keyword]".`
