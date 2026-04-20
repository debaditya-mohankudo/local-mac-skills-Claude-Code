---
name: local-mac-calendar
description: Use this skill when the user asks to read, show, list, add, create, delete, or remove local Apple Calendar events. Handles date ranges, specific calendars, and event details.
user-invocable: true
---

Read, add, or delete Apple Calendar events. All operations go through the **Python MCP server** (`mcp_server.py`) → Swift CLI binary (`~/bin/local-mac-tool`). Use MCP tool use directly — `local-mpc` is retired.

> See vault: `Projects/SWIFT_CLI_MCP_MIGRATION.md`

Default calendar: **Work** (iCloud). All read, add, and delete operations target the Work calendar unless the user explicitly specifies a different one.

**Step 1 — Determine the operation:**

Detect intent from the user's message:
- **read** — show/list/check events (default)
- **add** — "add event", "create event", "schedule X", "put X on calendar"
- **delete** — "delete event", "remove event", "cancel X"

Branch to the appropriate section below.

---

## ADD operation

**Step 2a — Extract event details:**

From the user's message extract:
- **title** (required) — event name
- **calendar** — target calendar name (default: `Work`)
- **start_date** (required) — convert to ISO-8601, e.g. `2026-04-10T09:00:00Z`; if no time given use `09:00:00Z`
- **end_date** — if not specified, defaults to start + 1 hour
- **notes** — any extra detail

**Step 3a — Create the event:**

MCP tool: `calendar_add_event`
```json
{
  "title": "TITLE",
  "calendar": "CALENDAR",
  "start_date": "2026-04-10T09:00:00Z",
  "end_date": "2026-04-10T10:00:00Z",
  "notes": "NOTES"
}
```

**Step 4a — Confirm:**

Output: `Added "[title]" to [calendar] on [ISO date]`

---

## DELETE operation

**Step 2b — Identify what to delete:**

Extract event title (or partial) and optionally a date or calendar name.

**Step 3b — Find the event:**

The tool automatically searches within a ±30-day window from today. If multiple matches, the tool returns a list and asks you to confirm which one. If exactly one match, the tool proceeds with deletion.

**Step 4b — Delete the event:**

MCP tool: `calendar_delete_event`
```json
{ "title": "TITLE", "calendar": "CALENDAR" }
```

**Step 5b — Confirm:**

Output: `Deleted "[title]" from [calendar].`

---

## READ operation

**Step 2c — Parse read filters:**

- **Date range**: extract from message. Defaults:
  - No qualifier → next 7 days
  - "today" → today only
  - "this week" → next 7 days
  - "this month" → next 30 days
  - "tomorrow" → tomorrow only
  - Explicit date → that day
- **Calendar filter**: default to `Work` only. Only include other calendars if the user explicitly names one.

**Step 3c — Convert date range to ISO-8601 and fetch events:**

MCP tool: `calendar_list_events`
```json
{ "start_date": "2026-04-11T00:00:00Z", "end_date": "2026-04-18T23:59:59Z" }
```

Returns JSON array with fields: `calendar`, `title`, `start`, `end`, `location`, `notes`, `isAllDay`.

**Step 4c — Apply filters and display:**

- Parse JSON response
- Sort events by start date/time
- Skip calendars: Birthdays, Siri Suggestions, Scheduled Reminders, Vedic Astro Events, Drik Panchang — unless explicitly requested
- Group by calendar and format for display:

```
## Calendar — [date range label]

### [Calendar Name]
- **Event Title**
  Mon, 23 Mar 2026 · 10:00 AM – 11:00 AM
  Notes: ...

**Total: X event(s)**
```

Rules:
- If no events found in range: `No events found for [range].`
- For all-day events, omit time and just show the date
- Only show Notes line if non-empty
- If calendar has no events after filtering, omit it
