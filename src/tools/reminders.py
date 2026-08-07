"""
reminders.py
------------
MCP tool handlers for Reminders.app via AppleScript, ported from
local-mac-tool/Sources/LocalMacMCP/RemindersTool.swift (which used native
EventKit — AppleScript's `tell application "Reminders"` covers the same
ground for list/create/complete/delete, referencing reminders by their
AppleScript `id` property, which is stable like EventKit's
calendarItemIdentifier).

Performance note: naive per-item AppleScript property access (`id of r`,
`due date of r`, ... inside a `repeat with r in reminders of lst`) is
pathologically slow — one Apple Event round-trip per property per item,
measured at ~24s for 14 items with just id+name. Fetching whole properties
in bulk (`id of every reminder of lst`) does the same work in one round-trip
per property per list — measured at ~9s for 45 items with all 6 fields.
Every script below uses the bulk form.

Record/field separators use ASCII control characters (unit/record
separator), not "|||"/"\\n" — reminder bodies can contain literal newlines,
which would corrupt naive newline-based record splitting.

Known gap vs. the Swift tool: recurrence (daily/weekly/monthly/yearly) is
NOT supported here — Reminders.app's AppleScript dictionary doesn't expose
recurrence-rule creation. A recurrence argument is accepted but ignored with
a note in the return value, rather than silently dropped without saying so.
"""
from __future__ import annotations

from local_process import run_osascript

_FIELD_SEP = "ASCII character 31"  # unit separator
_REC_SEP = "ASCII character 30"    # record separator


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _missing(s: str) -> str | None:
    return None if s in ("", "missing value") else s


def handle_list(list: str = None, include_completed: bool = False) -> dict | str:
    """List reminders. Optionally filter by list name."""
    list_clause = f'{{list "{_escape(list)}"}}' if list else "lists"

    script = f'''
        tell application "Reminders"
            set fSep to {_FIELD_SEP}
            set rSep to {_REC_SEP}
            set output to ""
            repeat with lst in {list_clause}
                set idList to id of every reminder of lst
                set nameList to name of every reminder of lst
                set completedList to completed of every reminder of lst
                set dueList to due date of every reminder of lst
                set bodyList to body of every reminder of lst
                set priorityList to priority of every reminder of lst
                set lstName to name of lst
                repeat with i from 1 to count of idList
                    if not (item i of completedList) then
                        set dueStr to ""
                        try
                            set dueStr to ((item i of dueList) as string)
                        end try
                        set bodyStr to ""
                        try
                            set bodyStr to ((item i of bodyList) as string)
                        end try
                        set output to output & (item i of idList) & fSep & (item i of nameList) & fSep & lstName & fSep & "false" & fSep & dueStr & fSep & bodyStr & fSep & (item i of priorityList) & rSep
                    end if
                end repeat
            end repeat
            if {str(include_completed).lower()} then
                repeat with lst in {list_clause}
                    set idList to id of every reminder of lst
                    set nameList to name of every reminder of lst
                    set completedList to completed of every reminder of lst
                    set dueList to due date of every reminder of lst
                    set bodyList to body of every reminder of lst
                    set priorityList to priority of every reminder of lst
                    set lstName to name of lst
                    repeat with i from 1 to count of idList
                        if (item i of completedList) then
                            set dueStr to ""
                            try
                                set dueStr to ((item i of dueList) as string)
                            end try
                            set bodyStr to ""
                            try
                                set bodyStr to ((item i of bodyList) as string)
                            end try
                            set output to output & (item i of idList) & fSep & (item i of nameList) & fSep & lstName & fSep & "true" & fSep & dueStr & fSep & bodyStr & fSep & (item i of priorityList) & rSep
                        end if
                    end repeat
                end repeat
            end if
            return output
        end tell
        '''
    result = run_osascript(script, timeout=60)
    if not result:
        return "No reminders found."

    entries = []
    for record in result.split(chr(30)):
        if not record:
            continue
        parts = record.split(chr(31))
        if len(parts) < 7:
            continue
        entries.append({
            "id": parts[0],
            "title": parts[1],
            "list": parts[2],
            "completed": parts[3] == "true",
            "dueDate": _missing(parts[4]),
            "notes": _missing(parts[5]),
            "priority": int(parts[6]) if parts[6].isdigit() else 0,
        })
    entries.sort(key=lambda e: e["completed"])
    return entries if entries else "No reminders found."


def handle_create(title: str, list: str = None, due_date: str = None, notes: str = None, recurrence: str = None) -> str:
    """Create a reminder. recurrence is NOT supported (AppleScript limitation) — accepted but ignored."""
    if not title:
        raise ValueError("Missing required argument: title")

    list_clause = f'list "{_escape(list)}"' if list else "default list"
    props = [f'name:"{_escape(title)}"']
    if notes:
        props.append(f'body:"{_escape(notes)}"')

    due_set = ""
    if due_date:
        # Build the date via AppleScript's `current date` + explicit component
        # assignment rather than parsing an ISO string literal (locale-fragile).
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Invalid due_date format. Use ISO-8601, e.g. 2026-04-11T09:00:00")
        due_set = f'''
            set dueD to current date
            set year of dueD to {dt.year}
            set month of dueD to {dt.month}
            set day of dueD to {dt.day}
            set hours of dueD to {dt.hour}
            set minutes of dueD to {dt.minute}
            set seconds of dueD to 0
            set due date of newReminder to dueD
        '''

    script = f'''
        tell application "Reminders"
            set targetList to {list_clause}
            set newReminder to make new reminder at end of targetList with properties {{{", ".join(props)}}}
            {due_set}
            return (name of targetList) & "|||" & (id of newReminder)
        end tell
        '''
    result = run_osascript(script)
    list_name = result.partition("|||")[0]
    msg = f"Created reminder '{title}' in '{list_name}'"
    if recurrence:
        msg += f" (recurrence '{recurrence}' NOT applied — unsupported via AppleScript)"
    return msg


def _act_on_reminder_script(reminder_id: str, action: str) -> str:
    """Bulk-fetch ids per list to find the matching index, then act on it by
    index (`reminder N of lst`) — avoids the slow per-item property scan."""
    escaped = _escape(reminder_id)
    return f'''
        tell application "Reminders"
            repeat with lst in lists
                set idList to id of every reminder of lst
                repeat with i from 1 to count of idList
                    if (item i of idList) is "{escaped}" then
                        set r to reminder i of lst
                        set rName to name of r
                        {action}
                        return rName
                    end if
                end repeat
            end repeat
            error "Reminder not found: {escaped}"
        end tell
        '''


def handle_complete(id: str) -> str:
    """Mark a reminder complete by its identifier."""
    if not id:
        raise ValueError("Missing required argument: id")
    title = run_osascript(_act_on_reminder_script(id, "set completed of r to true"))
    return f"Completed: '{title}'"


def handle_delete(id: str) -> str:
    """Delete a reminder by its identifier."""
    if not id:
        raise ValueError("Missing required argument: id")
    title = run_osascript(_act_on_reminder_script(id, "delete r"))
    return f"Deleted reminder '{title}'"
