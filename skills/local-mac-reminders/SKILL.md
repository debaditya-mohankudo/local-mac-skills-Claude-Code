---
name: local-mac-reminders
description: Use this skill when the user asks to read, show, list, add, create, delete, or remove Apple Reminders. Handles filtering by list name or completion status.
user-invocable: true
---

Read, add, or delete Apple Reminders. All operations go through the **Python MCP server** (`mcp_server.py`) → Swift CLI binary (`~/bin/local-mac-tool`). Use MCP tool use directly — `local-mpc` is retired.

> See vault: `Projects/SWIFT_CLI_MCP_MIGRATION.md`

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
- **title** (required) — the task text
- **list** — target list name (default: Reminders list)
- **due_date** — any date/time mentioned (convert to ISO-8601, e.g. `2026-04-11T09:00:00Z`; assume today if date not specified)
- **notes** — any extra detail after the task name

**Step 3a — Create the reminder:**

MCP tool: `reminders_create`
```json
{ "title": "TITLE", "list": "LIST", "due_date": "2026-04-11T09:00:00Z", "notes": "NOTES" }
```

**Step 4a — Confirm:**

Output: `Created reminder "[title]" in "[list]"`

---

## DELETE operation

**Step 2b — Identify what to delete:**

From the user's message extract the reminder title (or partial title) and optionally a list name.

**Step 3b — Find and confirm match:**

First, fetch reminders using the read operation below and find reminders whose title contains the search string (case-insensitive). If multiple matches, list them and ask the user to confirm which one. If exactly one match, use its ID from the response.

**Step 4b — Complete the reminder (mark as done):**

Use the reminder ID returned from the list operation:

MCP tool: `reminders_complete`
```json
{ "id": "REMINDER_ID" }
```

Alternatively, manually delete via the Reminders app if needed. The MCP tools support completing reminders (marking as done).

**Step 5b — Confirm:**

Output: `Completed: "[title]"`

> Note: The native implementation marks reminders as completed rather than deleting them. This is safer and aligns with macOS Reminders behavior.

---

## READ operation

**Step 2c — Parse read filters:**

- **Status filter**: `pending` (incomplete only, default), `completed`, or `all`
- **List filter**: if a specific list name is mentioned (e.g. "show reminders from home"), filter to that list only

**Step 3c — Fetch reminders:**

MCP tool: `reminders_list`
```json
{ "include_completed": false, "list": "LIST_NAME" }
```

Returns JSON array with fields: `id`, `title`, `list`, `completed`, `dueDate`, `notes`, `priority`.

**Step 4c — Apply filters and display:**

- Parse JSON response
- Filter by status: if user requested only pending, exclude completed=true; if requested completed, include only completed=true
- Filter by list name if specified (case-insensitive match)
- If no reminders match, say so clearly

Group by list name. Format:

```
## Reminders — [status label]

### [List Name]
- [ ] Task name  *(due: Mon, 21 Mar 2026)*
      Notes: ...
      ID: abc123def456
- [x] Completed task

**Total: X reminder(s)**
```

Rules:
- Use `[ ]` for incomplete, `[x]` for completed
- Only show the "due" line if a due date exists
- Only show the "Notes" line if notes are non-empty
- Include the `ID` field from the response so user can reference it for completion
- If a list has no matching reminders after filtering, omit it from the output
- If all reminders across all lists are empty after filtering, output: `No reminders found.`
