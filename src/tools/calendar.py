"""
calendar.py
-----------
Two unrelated subsystems, both ported from local-mac-tool/Sources/LocalMacMCP/:

1. list_events — EventKit via PyObjC (the AppleScript version cost ~50s per
   busy calendar and was removed). add_event/delete_event — Calendar.app via
   AppleScript, ported from CalendarTool.swift.

2. get_noise_summary — NOT Calendar.app at all. Ported from CalendarQueryTool.swift, which reads a separate
   market-intelligence SQLite DB (~/Documents/claude_cache_data/market-intel/
   market.sqlite, table `calendar`) for economic-event noise scoring
   (gold/crude/nifty/usdinr/dxy). Grooming had assumed these three would be
   Python aggregation over list_events — that assumption was wrong, caught
   by reading the actual Swift source before implementing.

Known condition: market.sqlite is a 0-byte file with no `calendar` table, so
get_noise_summary fails with "no such table". get_events_by_date and
get_upcoming_events originally read it too; they now read Calendar.app's
"market-watch" calendar (via list_events) instead, since that is where
market events actually live.
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


def _end_iso(d: str) -> str:
    # A bare YYYY-MM-DD end date means "through that day", not its midnight --
    # otherwise every event on the end day after 00:00 is silently dropped.
    return d if "T" in d else f"{d}T23:59:00Z"


def _local_dt(iso_str: str):
    from datetime import datetime
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    # Callers pass wall-clock dates ("2026-09-27" -> "...T00:00:00Z"); treat
    # them as local time, matching the AppleScript path, not as UTC.
    return dt.replace(tzinfo=None)


def _list_events_eventkit(start_iso: str, end_iso: str, calendar: str) -> list[dict] | None:
    """EventKit query; None when the framework or full calendar access is unavailable.

    Full access is a TCC grant on the process running this server (status 3);
    write-only (4) hides every calendar, so it counts as unavailable too.
    """
    try:
        import EventKit
        from Foundation import NSDate
    except ImportError:
        return None
    if EventKit.EKEventStore.authorizationStatusForEntityType_(EventKit.EKEntityTypeEvent) != 3:
        return None
    from datetime import datetime

    store = EventKit.EKEventStore.alloc().init()
    cals = list(store.calendarsForEntityType_(EventKit.EKEntityTypeEvent))
    if calendar:
        cals = [c for c in cals if calendar in (c.title(), c.calendarIdentifier())]
        if not cals:
            return []
    start = NSDate.dateWithTimeIntervalSince1970_(_local_dt(start_iso).timestamp())
    end = NSDate.dateWithTimeIntervalSince1970_(_local_dt(end_iso).timestamp())
    # Overlap semantics and recurrence expansion are both native here.
    pred = store.predicateForEventsWithStartDate_endDate_calendars_(start, end, cals)

    def iso(d):
        return datetime.fromtimestamp(d.timeIntervalSince1970()).strftime("%Y-%m-%dT%H:%M:%S")

    entries = [{
        "calendar": e.calendar().title(),
        "calendarId": e.calendar().calendarIdentifier(),
        "title": e.title(),
        "start": iso(e.startDate()),
        "end": iso(e.endDate()),
        "location": e.location() or None,
        "notes": e.notes() or None,
        "isAllDay": bool(e.isAllDay()),
    } for e in store.eventsMatchingPredicate_(pred)]
    entries.sort(key=lambda e: e["start"])
    return entries


def handle_list_events(start_date: str, end_date: str, calendar: str = "") -> list[dict]:
    """List calendar events overlapping [start_date, end_date] (YYYY-MM-DD or full ISO-8601; a bare end date covers that whole day). Pass calendar (title or identifier, e.g. "market-watch") to query one calendar. Recurring events are expanded. Returns events sorted by start, with local ISO start/end."""
    start_iso, end_iso = _iso(start_date), _end_iso(end_date)
    events = _list_events_eventkit(start_iso, end_iso, calendar)
    if events is None:
        raise RuntimeError(
            "EventKit full calendar access not granted to the process running this server "
            "(System Settings > Privacy & Security > Calendars > Full Access)")
    return events


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


_NOISE_RANK = {"high": 0, "medium": 1, "low": 2}


def _market_watch_events(start: str, end: str) -> list[dict]:
    # market.sqlite is empty (see module docstring); the live market-event
    # calendar is Calendar.app's "market-watch". Its generated events carry
    # "Type: ..." / "Noise: ..." lines in their notes -- surface those.
    events = handle_list_events(start, end, calendar="market-watch")
    for e in events:
        fields = {}
        for line in (e["notes"] or "").splitlines():
            key, sep, val = line.partition(":")
            if sep and key.strip() in ("Type", "Noise"):
                fields[key.strip().lower()] = val.strip()
        e["event_type"] = fields.get("type")
        e["noise_level"] = fields.get("noise")
    events.sort(key=lambda e: (e["start"][:10], _NOISE_RANK.get(e["noise_level"], 3)))
    return events


def handle_get_events_by_date(date: str) -> list[dict]:
    """Get market-watch calendar events (Calendar.app) on a specific date (YYYY-MM-DD), high-noise first."""
    if not date:
        raise ValueError("Missing required argument: date (YYYY-MM-DD)")
    return _market_watch_events(date, date)


def handle_get_upcoming_events(days_ahead: int = 7, from_date: str = "") -> list[dict]:
    """Get market-watch calendar events (Calendar.app) from from_date (default today) through days_ahead days, by date then noise level. The 7-day ambient-context read."""
    from datetime import date, timedelta
    start = date.fromisoformat(from_date) if from_date else date.today()
    return _market_watch_events(start.isoformat(), (start + timedelta(days=days_ahead)).isoformat())


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
