---
name: local-mac-calendar
description: Use this skill when the user asks to read, show, list, add, create, delete, or remove local Apple Calendar events. Handles date ranges, specific calendars, and event details.
user-invocable: true
---

Read, add, or delete Apple Calendar events via AppleScript.

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
- **start date/time** (required) — convert to `MM/DD/YYYY HH:MM:SS`; if no time given use `09:00:00`
- **end date/time** — if not specified, default to start + 1 hour
- **notes** — any extra detail

**Step 3a — Create the event:**

```bash
~/workspace/claude_for_mac_local/tools/calendar_add_event.sh "CALENDAR" "TITLE" "START" "END" ["NOTES"]
```

**Step 4a — Confirm:**

Output: `Added "[title]" to [calendar] on [date] from [start time] to [end time].`

---

## DELETE operation

**Step 2b — Identify what to delete:**

Extract event title (or partial) and optionally a date or calendar name.

**Step 3b — Find the event:**

Fetch a broad date range (±30 days from today) using the read tool below, then find events whose title contains the search string (case-insensitive). If multiple matches, list them and ask the user to confirm which one. If exactly one match, proceed.

**Step 4b — Delete the event:**

```bash
~/workspace/claude_for_mac_local/tools/calendar_delete_event.sh "CALENDAR" "EXACT TITLE"
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

**Step 3c — Fetch events:**

```bash
~/workspace/claude_for_mac_local/tools/calendar_list_events.sh "MM/DD/YYYY 00:00:00" "MM/DD/YYYY 23:59:59"
```

**Step 4c — Apply filters and display:**

- Sort events by start date/time
- Skip calendars: Birthdays, Siri Suggestions, Scheduled Reminders, Vedic Astro Events, Drik Panchang — unless explicitly requested
- Group by calendar

```
## Calendar — [date range label] — [DATE]

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
