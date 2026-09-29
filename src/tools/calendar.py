"""
calendar.py
-----------
Two unrelated subsystems, both ported from local-mac-tool/Sources/LocalMacMCP/:

1. list_events — EventKit via PyObjC (the AppleScript version cost ~50s per
   busy calendar and was removed). add_event/delete_event — EventKit too;
   their AppleScript versions (from CalendarTool.swift) enumerated the
   calendar via a `whose` query plus one Apple Event per candidate and hit
   the 120s timeout on market-watch before ever deleting.

2. get_noise_summary — NOT Calendar.app at all. Ported from CalendarQueryTool.swift, which reads a separate
   market-intelligence SQLite DB (~/Documents/claude_cache_data/market-intel/
   market.sqlite, table `calendar`) for economic-event noise scoring
   (gold/crude/nifty/usdinr/dxy). Grooming had assumed these three would be
   Python aggregation over list_events — that assumption was wrong, caught
   by reading the actual Swift source before implementing.

Process isolation: the long-lived MCP server process repeatedly lost sight of
the market-watch calendar (add_event "Calendar not found", list_events silently
[]) until reconnected, while fresh processes always saw it (task adf83977).
Trigger unproven, so every EventKit operation now runs in a short-lived child
(`python -m src.tools.calendar <op>`, JSON in on stdin / JSON out on stdout)
and no EventKit state survives between calls. The `_do_*` functions are the
in-process implementations and run only inside that child; the public
`handle_*` functions keep their names, signatures and docstrings.

Known condition: market.sqlite is a 0-byte file with no `calendar` table, so
get_noise_summary fails with "no such table". get_events_by_date and
get_upcoming_events originally read it too; they now read Calendar.app's
"market-watch" calendar (via list_events) instead, since that is where
market events actually live.
"""
from __future__ import annotations

import json
import subprocess
import sqlite3
import sys
import time
import traceback
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKER_TIMEOUT_S = 60

# list_events results, keyed (start, end, calendar). Bounded staleness: entries
# expire after _CACHE_TTL_S, and add/delete clear everything. Only non-empty
# successes are stored -- [] is what a blind calendar returned, so it is never
# remembered. Changes made outside this server (Calendar.app, iCloud) are
# visible only after the TTL.
_CACHE_TTL_S = 60
_list_cache: dict[tuple, tuple[float, list[dict]]] = {}
_MARKET_DB = Path.home() / "Documents" / "claude_cache_data" / "market-intel" / "market.sqlite"


def _iso(d: str) -> str:
    return d if "T" in d else f"{d}T00:00:00Z"


def _end_iso(d: str) -> str:
    # A bare YYYY-MM-DD end date means "through that day", not its midnight --
    # otherwise every event on the end day after 00:00 is silently dropped.
    return d if "T" in d else f"{d}T23:59:00Z"


def _local_dt(iso_str: str):
    from datetime import datetime
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    # Callers pass wall-clock dates ("2026-09-27" -> "...T00:00:00Z"); treat
    # them as local time, not as UTC.
    return dt.replace(tzinfo=None)


def _nsdate(dt):
    from Foundation import NSDate
    return NSDate.dateWithTimeIntervalSince1970_(dt.timestamp())


def _ns_iso(d) -> str:
    from datetime import datetime
    return datetime.fromtimestamp(d.timeIntervalSince1970()).strftime("%Y-%m-%dT%H:%M:%S")


def _store():
    """EventKit store with full calendar access, or None.

    Full access is a TCC grant on the process running this server (status 3);
    write-only (4) hides every calendar, so it counts as unavailable too.
    """
    import EventKit  # ImportError propagates: a missing framework is not "no access"
    if EventKit.EKEventStore.authorizationStatusForEntityType_(EventKit.EKEntityTypeEvent) != 3:
        return None
    return EventKit.EKEventStore.alloc().init()


def _require_store():
    store = _store()
    if store is None:
        raise RuntimeError(
            "EventKit full calendar access not granted to the process running this server "
            "(System Settings > Privacy & Security > Calendars > Full Access)")
    return store


def _calendars(store, calendar: str) -> list:
    import EventKit
    cals = list(store.calendarsForEntityType_(EventKit.EKEntityTypeEvent))
    if calendar:
        cals = [c for c in cals if calendar in (c.title(), c.calendarIdentifier())]
    return cals


def _one_calendar(store, calendar: str):
    cals = _calendars(store, calendar)
    if not cals:
        raise ValueError(f"Calendar not found: {calendar}")
    return cals[0]


def _events(store, start, end, cals) -> list:
    # Overlap semantics and recurrence expansion are both native here.
    pred = store.predicateForEventsWithStartDate_endDate_calendars_(_nsdate(start), _nsdate(end), cals)
    return list(store.eventsMatchingPredicate_(pred))


def _list_events_eventkit(start_iso: str, end_iso: str, calendar: str, store=None) -> list[dict] | None:
    """EventKit query; None when the framework or full calendar access is unavailable."""
    store = store or _store()
    if store is None:
        return None
    cals = _calendars(store, calendar)
    if calendar and not cals:
        # A silent [] here is indistinguishable from "no events" and hid a
        # blind-calendar failure behind plausible-looking data.
        raise ValueError(f"Calendar not found: {calendar}")
    entries = [{
        "calendar": e.calendar().title(),
        "calendarId": e.calendar().calendarIdentifier(),
        "title": e.title(),
        "start": _ns_iso(e.startDate()),
        "end": _ns_iso(e.endDate()),
        "location": e.location() or None,
        "notes": e.notes() or None,
        "isAllDay": bool(e.isAllDay()),
    } for e in _events(store, _local_dt(start_iso), _local_dt(end_iso), cals)]
    entries.sort(key=lambda e: e["start"])
    return entries


def _do_list_events(start_date: str, end_date: str, calendar: str = "") -> list[dict]:
    store = _require_store()
    return _list_events_eventkit(_iso(start_date), _end_iso(end_date), calendar, store)


def _do_add_event(title: str, start_date: str, calendar: str = "Work",
                  end_date: str = None, notes: str = None) -> str:
    if not title:
        raise ValueError("Missing required argument: title")
    if not start_date:
        raise ValueError("Missing required argument: start_date (ISO-8601)")
    import EventKit
    from datetime import timedelta

    store = _require_store()
    cal = _one_calendar(store, calendar)
    start = _local_dt(_iso(start_date))
    end = _local_dt(_iso(end_date)) if end_date else start + timedelta(hours=1)

    event = EventKit.EKEvent.eventWithEventStore_(store)
    event.setCalendar_(cal)
    event.setTitle_(title)
    event.setStartDate_(_nsdate(start))
    event.setEndDate_(_nsdate(end))
    if notes:
        event.setNotes_(notes)
    ok, err = store.saveEvent_span_commit_error_(event, EventKit.EKSpanThisEvent, True, None)
    if not ok:
        raise RuntimeError(f"EventKit save failed: {err}")
    return f"Added '{title}' to {calendar} on {start.isoformat()}"


def _do_delete_event(title: str, calendar: str = "Work") -> str:
    if not title:
        raise ValueError("Missing required argument: title")
    import EventKit
    from datetime import datetime, timedelta

    store = _require_store()
    cal = _one_calendar(store, calendar)
    now = datetime.now()
    matches = [e for e in _events(store, now - timedelta(days=30), now + timedelta(days=30), [cal])
               if title in (e.title() or "")]
    if not matches:
        raise ValueError(f"No events found matching '{title}' in {calendar}.")
    if len(matches) > 1:
        names = ", ".join(e.title() for e in matches)
        raise ValueError(f"Multiple events match '{title}': {names}. Please be more specific.")
    event = matches[0]
    name = event.title()
    ok, err = store.removeEvent_span_commit_error_(event, EventKit.EKSpanThisEvent, True, None)
    if not ok:
        raise RuntimeError(f"EventKit remove failed: {err}")
    return f"Deleted '{name}' from {calendar}."


# --- Process isolation: every EventKit call runs in a fresh child process ---

def _run_isolated(op: str, **kwargs):
    """Run `_do_<op>` in a short-lived child and return its result, re-raising its error type.

    The child inherits the TCC "responsible process" of this server, so the
    Calendars full-access grant applies unchanged.
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "src.tools.calendar", op],
            input=json.dumps(kwargs), capture_output=True, text=True,
            timeout=_WORKER_TIMEOUT_S, cwd=_REPO_ROOT,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"calendar {op} timed out after {_WORKER_TIMEOUT_S}s in EventKit worker")
    lines = proc.stdout.strip().splitlines()
    try:
        reply = json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError):
        raise RuntimeError(
            f"calendar {op} worker produced no result (exit {proc.returncode}): "
            f"{proc.stderr.strip()[-500:] or 'no stderr'}")
    if reply["ok"] and proc.returncode == 0:
        return reply["result"]
    err_type = {"ValueError": ValueError, "FileNotFoundError": FileNotFoundError}.get(
        reply["error_type"], RuntimeError)
    raise err_type(reply["error"])


def _worker_main(argv: list[str]) -> int:
    op = argv[0]
    fn = {"list_events": _do_list_events, "add_event": _do_add_event,
          "delete_event": _do_delete_event}.get(op)
    try:
        if fn is None:
            raise ValueError(f"Unknown calendar worker op: {op}")
        reply = {"ok": True, "result": fn(**json.loads(sys.stdin.read() or "{}"))}
    except Exception as e:  # relayed to the parent, which re-raises by type
        reply = {"ok": False, "error_type": type(e).__name__, "error": str(e)}
        traceback.print_exc()
        print(json.dumps(reply))
        return 1  # non-zero exit: an error must never look like success
    print(json.dumps(reply))
    return 0


def handle_list_events(start_date: str, end_date: str, calendar: str = "") -> list[dict]:
    """List calendar events overlapping [start_date, end_date] (YYYY-MM-DD or full ISO-8601; a bare end date covers that whole day). Pass calendar (title or identifier, e.g. "market-watch") to query one calendar. Recurring events are expanded. Returns events sorted by start, with local ISO start/end."""
    key = (start_date, end_date, calendar)
    hit = _list_cache.get(key)
    if hit and time.monotonic() - hit[0] < _CACHE_TTL_S:
        return [dict(e) for e in hit[1]]  # copies: _market_watch_events mutates and sorts its list
    events = _run_isolated("list_events", start_date=start_date, end_date=end_date, calendar=calendar)
    if events:
        _list_cache[key] = (time.monotonic(), [dict(e) for e in events])
    return events


def handle_add_event(title: str, start_date: str, calendar: str = "Work",
                     end_date: str = None, notes: str = None) -> str:
    """Add a calendar event."""
    _list_cache.clear()  # cleared before and after: a failed write may still have changed the store
    try:
        return _run_isolated("add_event", title=title, start_date=start_date, calendar=calendar,
                             end_date=end_date, notes=notes)
    finally:
        _list_cache.clear()


def handle_delete_event(title: str, calendar: str = "Work") -> str:
    """Delete a calendar event by title (must be unique match within ±30 days)."""
    _list_cache.clear()
    try:
        return _run_isolated("delete_event", title=title, calendar=calendar)
    finally:
        _list_cache.clear()


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
        noise_assets = json.loads(noise_assets_str) if noise_assets_str else []
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


if __name__ == "__main__":
    sys.exit(_worker_main(sys.argv[1:]))
