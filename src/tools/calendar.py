"""
calendar.py
-----------
Two unrelated subsystems, both ported from local-mac-tool/Sources/LocalMacMCP/:

1. list_events/add_event/delete_event — Calendar.app via AppleScript, ported
   from CalendarTool.swift (which used native EventKit; AppleScript's
   `tell application "Calendar"` covers the same CRUD ground).

2. get_events_by_date/get_upcoming_events/get_noise_summary — NOT Calendar.app
   at all. Ported from CalendarQueryTool.swift, which reads a separate
   market-intelligence SQLite DB (~/Documents/claude_cache_data/market-intel/
   market.sqlite, table `calendar`) for economic-event noise scoring
   (gold/crude/nifty/usdinr/dxy). Grooming had assumed these three would be
   Python aggregation over list_events — that assumption was wrong, caught
   by reading the actual Swift source before implementing.

Known pre-existing condition (not caused by this port): market.sqlite exists
but is a 0-byte file with no `calendar` table — these three actions already
fail with "no such table" in the current Swift-backed implementation too.
Ported faithfully so they work once/if that table is populated elsewhere;
not something to fix as part of removing the Swift build.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from local_process import run_osascript

_MARKET_DB = Path.home() / "Documents" / "claude_cache_data" / "market-intel" / "market.sqlite"


def _iso(d: str) -> str:
    return d if "T" in d else f"{d}T00:00:00Z"


def _escape(s: str) -> str:
    return s.replace('"', '\\"')


def _parse_iso_for_applescript(iso_str: str) -> tuple[int, int, int, int, int]:
    from datetime import datetime
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.year, dt.month, dt.day, dt.hour, dt.minute


def _applescript_date_expr(iso_str: str, var: str) -> str:
    y, mo, d, h, mi = _parse_iso_for_applescript(iso_str)
    return f'''
        set {var} to current date
        set year of {var} to {y}
        set month of {var} to {mo}
        set day of {var} to {d}
        set hours of {var} to {h}
        set minutes of {var} to {mi}
        set seconds of {var} to 0
        '''


def handle_list_events(start_date: str, end_date: str) -> dict | str:
    """List calendar events between ISO-8601 start and end dates (YYYY-MM-DD or full ISO-8601)."""
    start_iso, end_iso = _iso(start_date), _iso(end_date)
    start_setup = _applescript_date_expr(start_iso, "startD")
    end_setup = _applescript_date_expr(end_iso, "endD")

    # Performance chain found via live testing, each layer a distinct bug:
    # 1. Naive per-item access (`repeat with e in evts: ... summary of e`)
    #    times out even for small result sets — one Apple Event round-trip
    #    per property per ITEM.
    # 2. Storing a `whose`-filtered reference then bulk-fetching a property on
    #    it (`set evts to (events of cal whose ...)` then `summary of evts`)
    #    fails outright with "Can't get summary of {...}" (-1728).
    # 3. Inlining the `whose` filter per property (`summary of every event of
    #    cal whose ...`, `start date of every event of cal whose ...`, etc.)
    #    works, but re-evaluates the filter once per PROPERTY — 6 evaluations
    #    against a 595-event calendar ("claude", the busiest here) times out
    #    past 120s.
    # 4. Fix: `properties of every event of cal whose ...` fetches ALL fields
    #    in one round-trip per calendar (measured ~44-49s for the busiest
    #    calendar here) as a list of plain AppleScript records — records, not
    #    app-object references, so a follow-up per-item field-access loop on
    #    them is instant (no further Apple Events needed).
    #
    # Also: iterating ALL `calendars` (including Birthdays/Holidays/Scheduled
    # Reminders/Siri Suggestions) is separately too slow regardless of the
    # fetch strategy — those are large Apple-managed derived/subscribed
    # calendars with years of recurring data, not real event calendars.
    # Swift's original used EventKit's `calendars(for: .event)`, which
    # excludes them automatically; AppleScript has no equivalent type filter,
    # so they're excluded by substring match here (exact-name match wasn't
    # robust enough — this account has multiple differently-named
    # holiday/birthday calendars) to match Swift's actual scope, not to
    # silently narrow it further.
    script = f'''
        tell application "Calendar"
            {start_setup}
            {end_setup}
            set output to ""
            repeat with cal in calendars
                set calName to name of cal
                if calName does not contain "Birthday" and calName does not contain "Holiday" and calName does not contain "holiday" and calName does not contain "Scheduled Reminders" and calName does not contain "Siri Suggestions" then
                    set props to properties of every event of cal whose start date >= startD and start date <= endD
                    repeat with p in props
                        set locStr to location of p
                        if locStr is missing value then set locStr to ""
                        set descStr to description of p
                        if descStr is missing value then set descStr to ""
                        set output to output & calName & (ASCII character 31) & (summary of p) & (ASCII character 31) & ((start date of p) as string) & (ASCII character 31) & ((end date of p) as string) & (ASCII character 31) & locStr & (ASCII character 31) & descStr & (ASCII character 31) & (allday event of p) & (ASCII character 30)
                    end repeat
                end if
            end repeat
            return output
        end tell
        '''
    # 240s: even the fixed single-round-trip-per-calendar approach measured
    # ~45-50s for this account's busiest calendar (595 events) — with several
    # such calendars in a typical query, the realistic worst case is minutes,
    # not seconds. This is a genuine Calendar.app AppleScript performance
    # ceiling, not something further query restructuring fixes.
    result = run_osascript(script, timeout=240)
    if not result:
        return f"No events found between {start_date} and {end_date}."

    entries = []
    for record in result.split(chr(30)):
        if not record:
            continue
        parts = record.split(chr(31))
        if len(parts) < 7:
            continue
        entries.append({
            "calendar": parts[0],
            "title": parts[1],
            "start": parts[2],
            "end": parts[3],
            "location": parts[4] or None,
            "notes": parts[5] or None,
            "isAllDay": parts[6] == "true",
        })
    return entries if entries else f"No events found between {start_date} and {end_date}."


def handle_add_event(title: str, start_date: str, calendar: str = "Work",
                     end_date: str = None, notes: str = None) -> str:
    """Add a calendar event."""
    if not title:
        raise ValueError("Missing required argument: title")
    if not start_date:
        raise ValueError("Missing required argument: start_date (ISO-8601)")

    start_iso = _iso(start_date)
    if end_date:
        end_iso = _iso(end_date)
    else:
        from datetime import datetime, timedelta
        dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00")) + timedelta(hours=1)
        end_iso = dt.isoformat()

    start_setup = _applescript_date_expr(start_iso, "startD")
    end_setup = _applescript_date_expr(end_iso, "endD")
    escaped_title = _escape(title)
    escaped_cal = _escape(calendar)
    # Calendar.app's AppleScript property is `description`, not `notes` (renamed
    # at some point — found via live testing, `notes` errors with -1700). Must
    # also be set as a separate statement after creation, not in the initial
    # `make new event ... with properties {...}` record (that combination
    # errors too, a real Calendar.app AppleScript quirk).
    notes_set = f'set description of newEvent to "{_escape(notes)}"' if notes else ""

    script = f'''
        tell application "Calendar"
            {start_setup}
            {end_setup}
            set targetCal to calendar "{escaped_cal}"
            set newEvent to make new event at end of events of targetCal with properties {{summary:"{escaped_title}", start date:startD, end date:endD}}
            {notes_set}
            return (startD as string)
        end tell
        '''
    result = run_osascript(script, timeout=120)
    return f"Added '{title}' to {calendar} on {result}"


def handle_delete_event(title: str, calendar: str = "Work") -> str:
    """Delete a calendar event by title (must be unique match within ±30 days)."""
    if not title:
        raise ValueError("Missing required argument: title")

    escaped_title = _escape(title)
    escaped_cal = _escape(calendar)
    script = f'''
        tell application "Calendar"
            set targetCal to calendar "{escaped_cal}"
            set now to current date
            set rangeStart to now - (30 * days)
            set rangeEnd to now + (30 * days)
            set candidates to (events of targetCal whose start date >= rangeStart and start date <= rangeEnd)
            set matches to {{}}
            repeat with e in candidates
                if (summary of e) contains "{escaped_title}" then
                    set end of matches to e
                end if
            end repeat
            if (count of matches) is 0 then
                error "No events found matching '{escaped_title}' in {escaped_cal}."
            end if
            if (count of matches) > 1 then
                set names to ""
                repeat with e in matches
                    set names to names & (summary of e) & ", "
                end repeat
                error "Multiple events match '{escaped_title}': " & names & "Please be more specific."
            end if
            set theEvent to item 1 of matches
            set eventName to summary of theEvent
            delete theEvent
            return eventName
        end tell
        '''
    result = run_osascript(script, timeout=120)
    return f"Deleted '{result}' from {calendar}."


# --- Market-intel calendar (separate SQLite DB, nothing to do with Calendar.app) ---

def _query_events_by_date(date_str: str) -> list[dict]:
    if not _MARKET_DB.exists():
        raise FileNotFoundError(f"Database not found at {_MARKET_DB}")
    con = sqlite3.connect(f"file:{_MARKET_DB}?mode=ro", uri=True)
    try:
        rows = con.execute(
            """
            SELECT date, event_type, label, noise_level, noise_assets, notes, reference_month, confirmed
            FROM calendar
            WHERE date = ?
            ORDER BY CASE noise_level WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END
            """,
            (date_str,),
        ).fetchall()
    finally:
        con.close()
    return _rows_to_events(rows)


def _query_upcoming_events(days_ahead: int, from_date: str) -> list[dict]:
    if not _MARKET_DB.exists():
        raise FileNotFoundError(f"Database not found at {_MARKET_DB}")
    from datetime import date, timedelta
    start = date.fromisoformat(from_date) if from_date else date.today()
    end = start + timedelta(days=days_ahead)

    con = sqlite3.connect(f"file:{_MARKET_DB}?mode=ro", uri=True)
    try:
        rows = con.execute(
            """
            SELECT date, event_type, label, noise_level, noise_assets, notes, reference_month, confirmed
            FROM calendar
            WHERE date >= ? AND date <= ?
            ORDER BY date ASC, CASE noise_level WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END
            """,
            (start.isoformat(), end.isoformat()),
        ).fetchall()
    finally:
        con.close()
    return _rows_to_events(rows)


def _rows_to_events(rows) -> list[dict]:
    import json
    events = []
    for date, event_type, label, noise_level, noise_assets_str, notes, reference_month, confirmed in rows:
        try:
            noise_assets = json.loads(noise_assets_str) if noise_assets_str else []
        except json.JSONDecodeError:
            noise_assets = []
        events.append({
            "date": date,
            "event_type": event_type,
            "label": label,
            "noise_level": noise_level,
            "noise_assets": noise_assets,
            "notes": notes,
            "reference_month": reference_month,
            "confirmed": bool(confirmed),
        })
    return events


def handle_get_events_by_date(date: str) -> dict:
    """Get market calendar events from SQLite for a specific date (YYYY-MM-DD)."""
    if not date:
        raise ValueError("Missing required argument: date (YYYY-MM-DD)")
    return _query_events_by_date(date)


def handle_get_upcoming_events(days_ahead: int = 7, from_date: str = "") -> dict:
    """Get upcoming market calendar events from SQLite."""
    return _query_upcoming_events(days_ahead, from_date)


def handle_get_noise_summary(date: str) -> dict:
    """Get per-asset noise summary for a date from SQLite calendar."""
    if not date:
        raise ValueError("Missing required argument: date (YYYY-MM-DD)")
    events = _query_events_by_date(date)
    assets = ["gold", "crude", "nifty", "usdinr", "dxy"]
    noise_scores = {}
    for asset in assets:
        max_level = "low"
        for event in events:
            if asset in event["noise_assets"]:
                if event["noise_level"] == "high":
                    max_level = "high"
                elif event["noise_level"] == "medium" and max_level != "high":
                    max_level = "medium"
        noise_scores[asset] = max_level

    return {
        "date": date,
        "events_count": len(events),
        "high_noise_events": sum(1 for e in events if e["noise_level"] == "high"),
        "noise_assets": noise_scores,
        "events": events,
    }
