---
name: local-mac-reminders
description: Use this skill when the user asks to read, show, list, add, create, delete, or remove Apple Reminders. Handles filtering by list name or completion status.
user-invocable: true
---

Read, add, or delete Apple Reminders via AppleScript.

**Step 1 — Determine the operation:**

Detect the intent from the user's message:

- **read** — show/list/check reminders (default)
- **add** — "add reminder", "create reminder", "remind me to X"
- **delete** — "delete reminder", "remove reminder"

Then branch to the appropriate step below.

---

## ADD operation

**Step 2a — Extract reminder details:**

From the user's message extract:
- **name** (required) — the task text
- **list** — target list name (default: `Reminders`)
- **due date** — any date/time mentioned (convert to `MM/DD/YYYY HH:MM:SS` format, assume current year if not specified)
- **notes** — any extra detail after the task name

**Step 3a — Create the reminder:**

```bash
~/workspace/claude_for_mac_local/tools/reminders_add.sh "LIST" "NAME" ["DUE_DATE"] ["NOTES"]
```

**Step 4a — Confirm:**

Output: `Added reminder "[name]" to [list][due date if set].`

---

## DELETE operation

**Step 2b — Identify what to delete:**

From the user's message extract the reminder name (or partial name) and optionally a list name.

**Step 3b — Find and confirm match:**

First, fetch all reminders using the read tool below and find reminders whose name contains the search string (case-insensitive). If multiple matches, list them and ask the user to confirm which one. If exactly one match, proceed.

**Step 4b — Delete the reminder:**

```bash
~/workspace/claude_for_mac_local/tools/reminders_delete.sh "LIST" "EXACT NAME"
```

**Step 5b — Confirm:**

Output: `Deleted reminder "[name]" from [list].`

---

## READ operation

**Step 2c — Parse read filters:**

- **Status filter**: `pending` (incomplete only), `completed`, or `all` (default: `all`)
- **List filter**: if a specific list name is mentioned (e.g. "show reminders from home"), filter to that list only

**Step 3c — Fetch reminders:**

```bash
~/workspace/claude_for_mac_local/tools/reminders_list.sh [STATUS]
```

**Step 4c — Apply filters and display:**

- Split output lines on `\t` to get: list, name, completed, due, notes
- Apply list filter if specified (case-insensitive match on list name)
- If no reminders match the filter, say so clearly

Group by list name. Format:

```
## Reminders — [status label] — [DATE]

### [List Name]
- [ ] Task name  *(due: Mon, 21 Mar 2026)*
      Notes: ...
- [x] Completed task

**Total: X reminder(s)**
```

Rules:
- Use `[ ]` for incomplete, `[x]` for completed
- Only show the "due" line if a due date exists
- Only show the "Notes" line if notes are non-empty
- If a list has no matching reminders after filtering, omit it from the output
- If all reminders across all lists are empty after filtering, output: `No reminders found matching your filter.`
