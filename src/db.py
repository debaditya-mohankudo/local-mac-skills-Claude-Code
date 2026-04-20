"""
db.py — SQLite helper layer for news articles, calendar events, and FII/DII data.

Database: ~/Documents/claude_cache_data/market-intel/market.sqlite (single file, 3 tables)

Tables:
  news      — all news articles, deduplicated
  calendar  — market calendar events (NSE F&O, MCX, COMEX, SHFE, CPI/PPI)
  fii_dii   — FII/DII daily flow history (NSE format dates)

Public API:
  insert_articles(articles, date_str)          → insert with dedup
  search_articles(query, date_from, date_to,
                  source, article_type, limit)  → keyword/filter search
  get_events_for_date(date_str)                → events on a specific date
  get_upcoming_events(days_ahead, from_date)   → events in next N days
  seed_calendar_2026()                         → idempotent — seeds all 2026 events
  load_fii_dii_history()                       → all FII/DII records sorted by date
  upsert_fii_dii_entry(entry)                  → insert or skip by date
  get_fii_dii_for_date(nse_date)               → single FII/DII record or None

Internal:
  db_conn()  — context manager: yields the shared connection inside a transaction.
               Commits on clean exit, rolls back on exception.
               Use for all reads and writes to ensure atomicity and speed.
"""

from __future__ import annotations

import atexit
import os
from collections import namedtuple
from contextlib import contextmanager
from datetime import date, timedelta
from typing import Generator

import json
import sqlite3

# ── Paths ─────────────────────────────────────────────────────────────────────
# Consolidated to cache: ~/Documents/claude_cache_data/market-intel/ (as of 2026-03-31)

SQLITE_PATH = os.path.expanduser("~/Documents/claude_cache_data/market-intel/market.sqlite")
_DB_DIR = os.path.dirname(SQLITE_PATH)

# ── Singleton connection ───────────────────────────────────────────────────────

_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        os.makedirs(_DB_DIR, exist_ok=True)
        _conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
        _conn.isolation_level = None  # manual transaction control
        _init_schema(_conn)
        atexit.register(_close_conn)
    return _conn


def _close_conn() -> None:
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


@contextmanager
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    """
    Yield the shared SQLite connection inside an explicit transaction.

    Commits on clean exit, rolls back on any exception.
    Batch writes (insert_articles, seed_calendar_2026) run as a single
    transaction — dramatically faster than per-statement autocommit.
    """
    conn = _get_conn()
    conn.execute("BEGIN")
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news (
            date        TEXT NOT NULL,
            title       TEXT NOT NULL,
            source      TEXT,
            url         TEXT,
            summary     TEXT,
            time        TEXT,
            published   TEXT,
            type        TEXT,
            dedup_key   TEXT PRIMARY KEY
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_news_date ON news(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_news_type ON news(type)")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS calendar (
            date            TEXT NOT NULL,
            event_type      TEXT NOT NULL,
            label           TEXT,
            noise_level     TEXT,
            noise_assets    TEXT,
            notes           TEXT,
            reference_month TEXT,
            confirmed       INTEGER,
            dedup_key       TEXT PRIMARY KEY
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_calendar_date ON calendar(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_calendar_type ON calendar(event_type)")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS fii_dii (
            date      TEXT PRIMARY KEY,
            fii_buy   REAL,
            fii_sell  REAL,
            fii_net   REAL,
            dii_buy   REAL,
            dii_sell  REAL,
            dii_net   REAL,
            date_iso  TEXT
        )
    """)
    # Migration: add date_iso column if missing (idempotent)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(fii_dii)").fetchall()]
    if "date_iso" not in cols:
        conn.execute("ALTER TABLE fii_dii ADD COLUMN date_iso TEXT")
    # Backfill date_iso for any rows where it's NULL
    from datetime import datetime as _dt_init
    rows = conn.execute("SELECT date FROM fii_dii WHERE date_iso IS NULL").fetchall()
    for (d,) in rows:
        try:
            iso = _dt_init.strptime(d, "%d-%b-%Y").strftime("%Y-%m-%d")
            conn.execute("UPDATE fii_dii SET date_iso = ? WHERE date = ?", [iso, d])
        except ValueError:
            pass
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fii_dii_date_iso ON fii_dii(date_iso)")


# ── Row types ─────────────────────────────────────────────────────────────────

_NewsRow = namedtuple("NewsRow", [
    "date", "title", "source", "url", "summary", "time", "published", "type", "dedup_key",
])

_CalendarRow = namedtuple("CalendarRow", [
    "date", "event_type", "label", "noise_level", "noise_assets",
    "notes", "reference_month", "confirmed", "dedup_key",
])

_FiiDiiRow = namedtuple("FiiDiiRow", [
    "date", "fii_buy", "fii_sell", "fii_net", "dii_buy", "dii_sell", "dii_net",
])


# ── News helpers ──────────────────────────────────────────────────────────────

def _dedup_key(article: dict) -> str:
    source = (article.get("source") or "").lower().strip()
    title = (article.get("title") or "").lower().strip()
    return f"{source}::{title}"


def insert_articles(articles: list[dict], date_str: str) -> dict:
    """
    Insert articles into the news table, skipping duplicates.

    Dedup key = source.lower() + '::' + title.lower().strip()
    All inserts run in a single transaction.

    Args:
        articles: list of article dicts (title, source, url, summary, time, type)
        date_str: YYYY-MM-DD string (the fetch date)

    Returns:
        {'inserted': int, 'skipped': int, 'total_in_db': int}
    """
    inserted = 0
    skipped = 0
    with db_conn() as conn:
        for art in articles:
            key = _dedup_key(art)
            existing = conn.execute(
                "SELECT 1 FROM news WHERE dedup_key = ?", [key]
            ).fetchone()
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO news
                        (date, title, source, url, summary, time, published, type, dedup_key)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        date_str,
                        art.get("title"),
                        art.get("source"),
                        art.get("url"),
                        art.get("summary"),
                        art.get("time"),
                        art.get("published"),
                        art.get("type"),
                        key,
                    ],
                )
                inserted += 1
            else:
                skipped += 1
        total = conn.execute("SELECT COUNT(*) FROM news").fetchone()[0]
    return {"inserted": inserted, "skipped": skipped, "total_in_db": total}


def _row_to_article(row: _NewsRow) -> dict:
    d = row._asdict()
    if d["date"] is not None:
        d["date"] = str(d["date"])
    return d


def search_articles(
    query: str = "",
    date_from: str = "",
    date_to: str = "",
    source: str = "",
    article_type: str = "",
    limit: int = 20,
) -> list[dict]:
    """
    Search news articles.

    Args:
        query:        Keyword to match against title + summary (case-insensitive)
        date_from:    YYYY-MM-DD lower bound (inclusive)
        date_to:      YYYY-MM-DD upper bound (inclusive)
        source:       Filter by source name (partial match, case-insensitive)
        article_type: Filter by type label, e.g. "Escalation", "Supply Impact"
        limit:        Max results to return (default 20)

    Returns:
        List of article dicts, most recent first.
    """
    sql = (
        "SELECT date, title, source, url, summary, time, published, type, dedup_key "
        "FROM news WHERE 1=1"
    )
    params: list = []

    if date_from:
        sql += " AND date >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND date <= ?"
        params.append(date_to)
    if source:
        sql += " AND source LIKE ?"
        params.append(f"%{source}%")
    if article_type:
        sql += " AND type LIKE ?"
        params.append(f"%{article_type}%")
    if query:
        sql += " AND (title LIKE ? OR summary LIKE ?)"
        params.append(f"%{query}%")
        params.append(f"%{query}%")

    sql += " ORDER BY date DESC LIMIT ?"
    params.append(limit)

    with db_conn() as conn:
        rows = [_NewsRow(*r) for r in conn.execute(sql, params).fetchall()]
    return [_row_to_article(r) for r in rows]


# ── Calendar helpers ──────────────────────────────────────────────────────────

def _cal_dedup_key(event: dict) -> str:
    return f"{event.get('date', '')}::{event.get('event_type', '')}"


_CAL_SELECT = (
    "SELECT date, event_type, label, noise_level, noise_assets, "
    "notes, reference_month, confirmed, dedup_key FROM calendar"
)

_NOISE_CASE = "CASE noise_level WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END"


def _row_to_event(row: _CalendarRow) -> dict:
    d = row._asdict()
    if d["date"] is not None:
        d["date"] = str(d["date"])
    if isinstance(d["noise_assets"], str):
        try:
            d["noise_assets"] = json.loads(d["noise_assets"])
        except (json.JSONDecodeError, TypeError):
            d["noise_assets"] = []
    return d


def get_events_for_date(date_str: str) -> list[dict]:
    """
    Return all calendar events on the given date.

    Args:
        date_str: YYYY-MM-DD

    Returns:
        List of event dicts sorted by noise_level (high first).
    """
    with db_conn() as conn:
        rows = [_CalendarRow(*r) for r in conn.execute(
            f"{_CAL_SELECT} WHERE date = ? ORDER BY {_NOISE_CASE}",
            [date_str],
        ).fetchall()]
    return [_row_to_event(r) for r in rows]


def get_upcoming_events(days_ahead: int = 7, from_date: str = "") -> list[dict]:
    """
    Return all calendar events in the next N days (inclusive of from_date).

    Args:
        days_ahead: Number of days to look ahead (default 7)
        from_date:  YYYY-MM-DD start date (default: today)

    Returns:
        List of event dicts sorted by date, then noise_level.
    """
    start = date.fromisoformat(from_date) if from_date else date.today()
    end = start + timedelta(days=days_ahead)

    with db_conn() as conn:
        rows = [_CalendarRow(*r) for r in conn.execute(
            f"{_CAL_SELECT} WHERE date >= ? AND date <= ? ORDER BY date, {_NOISE_CASE}",
            [start.isoformat(), end.isoformat()],
        ).fetchall()]
    return [_row_to_event(r) for r in rows]


# ── Calendar seeder ───────────────────────────────────────────────────────────

def _upsert_calendar_event(conn: sqlite3.Connection, event: dict) -> bool:
    """Insert or update a calendar event by dedup_key. Returns True if inserted."""
    key = _cal_dedup_key(event)
    noise_assets = json.dumps(event.get("noise_assets") or [])
    existing = conn.execute(
        "SELECT 1 FROM calendar WHERE dedup_key = ?", [key]
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE calendar SET
                date=?, event_type=?, label=?, noise_level=?, noise_assets=?,
                notes=?, reference_month=?, confirmed=?
            WHERE dedup_key=?
            """,
            [
                event.get("date"), event.get("event_type"), event.get("label"),
                event.get("noise_level"), noise_assets, event.get("notes"),
                event.get("reference_month"), event.get("confirmed"), key,
            ],
        )
        return False
    else:
        conn.execute(
            """
            INSERT INTO calendar
                (date, event_type, label, noise_level, noise_assets,
                 notes, reference_month, confirmed, dedup_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                event.get("date"), event.get("event_type"), event.get("label"),
                event.get("noise_level"), noise_assets, event.get("notes"),
                event.get("reference_month"), event.get("confirmed"), key,
            ],
        )
        return True


def seed_calendar_2026() -> dict:
    """
    Idempotent seeder — inserts all known 2026 market calendar events.
    All upserts run in a single transaction.

    Categories seeded:
      - LBMA bank holidays (England & Wales — London Gold Fix does not run)
      - NSE trading holidays (Republic Day, Holi, Good Friday, etc.)
      - NSE F&O weekly expiry (every Thursday)
      - NSE F&O monthly expiry (last Thursday of each month)
      - MCX Gold expiry (Feb, Apr, Jun, Aug, Oct, Dec)
      - MCX Crude expiry (Jan–Nov, 19th of preceding month adjusted)
      - COMEX Gold roll start + LTD (Feb, Apr, Jun, Aug, Oct, Dec)
      - SHFE Gold LTD (monthly, 15th adjusted)
      - US CPI release dates
      - US PPI release dates
      - ECB rate decisions (8 meetings, full year 2026)

    Returns:
        {'seeded': int, 'updated': int, 'total_in_db': int}
    """
    from datetime import date as _date

    events = []

    # ── NSE F&O weekly and monthly Thursday expiries ──────────────────────────
    nse_monthly = {
        "2026-01-29", "2026-02-26", "2026-03-26", "2026-04-30",
        "2026-05-28", "2026-06-25", "2026-07-30", "2026-08-27",
        "2026-09-24", "2026-10-29", "2026-11-26", "2026-12-31",
    }

    d = _date(2026, 1, 1)
    while d.weekday() != 3:  # 3 = Thursday
        d += timedelta(days=1)
    while d.year == 2026:
        ds = d.isoformat()
        is_monthly = ds in nse_monthly
        events.append({
            "date": ds,
            "event_type": "nse_fo_monthly" if is_monthly else "nse_fo_weekly",
            "label": f"NSE F&O {'Monthly' if is_monthly else 'Weekly'} Expiry — {d.strftime('%b %d')}",
            "noise_assets": ["nifty"],
            "noise_level": "medium" if is_monthly else "low",
            "notes": "Nifty + stock options expire. Intraday volatility, pin risk. Not a war signal.",
        })
        d += timedelta(days=7)

    # ── MCX Gold expiry ────────────────────────────────────────────────────────
    for ds, contract in [
        ("2026-02-05", "Feb 2026"), ("2026-04-03", "Apr 2026"),
        ("2026-06-05", "Jun 2026"), ("2026-08-05", "Aug 2026"),
        ("2026-10-05", "Oct 2026"), ("2026-12-04", "Dec 2026"),
    ]:
        events.append({
            "date": ds, "event_type": "mcx_gold",
            "label": f"MCX Gold {contract} Expiry",
            "noise_assets": ["gold"], "noise_level": "medium",
            "notes": "MCX Gold expiry — spread widening, volume shift. Gold drop ≠ ceasefire signal.",
        })

    # ── MCX Crude expiry ───────────────────────────────────────────────────────
    for ds, contract in [
        ("2026-01-19", "Feb 2026"), ("2026-02-19", "Mar 2026"),
        ("2026-03-19", "Apr 2026"), ("2026-04-17", "May 2026"),
        ("2026-05-19", "Jun 2026"), ("2026-06-19", "Jul 2026"),
        ("2026-07-17", "Aug 2026"), ("2026-08-19", "Sep 2026"),
        ("2026-09-18", "Oct 2026"), ("2026-10-19", "Nov 2026"),
        ("2026-11-19", "Dec 2026"),
    ]:
        events.append({
            "date": ds, "event_type": "mcx_crude",
            "label": f"MCX Crude {contract} Expiry",
            "noise_assets": ["crude"], "noise_level": "medium",
            "notes": "MCX Crude expiry — intraday Brent/WTI roll volatility. Verify WTI NYMEX volumes.",
        })

    # ── COMEX Gold roll start ─────────────────────────────────────────────────
    for ds, contract in [
        ("2026-02-11", "Feb 2026"), ("2026-04-14", "Apr 2026"),
        ("2026-06-12", "Jun 2026"), ("2026-08-13", "Aug 2026"),
        ("2026-10-14", "Oct 2026"), ("2026-12-15", "Dec 2026"),
    ]:
        events.append({
            "date": ds, "event_type": "comex_roll_start",
            "label": f"COMEX Gold {contract} Roll Period Starts",
            "noise_assets": ["gold"], "noise_level": "high",
            "notes": "COMEX roll start — OI shifts to next contract over ~2 weeks. Gold may gap/spread.",
        })

    # ── COMEX Gold LTD ────────────────────────────────────────────────────────
    for ds, contract in [
        ("2026-02-25", "Feb 2026"), ("2026-04-28", "Apr 2026"),
        ("2026-06-26", "Jun 2026"), ("2026-08-27", "Aug 2026"),
        ("2026-10-28", "Oct 2026"), ("2026-12-29", "Dec 2026"),
    ]:
        events.append({
            "date": ds, "event_type": "comex_ltd",
            "label": f"COMEX Gold {contract} Last Trading Day",
            "noise_assets": ["gold"], "noise_level": "high",
            "notes": "COMEX Gold LTD — sharp intraday moves. Gold drop on LTD ≠ ceasefire signal.",
        })

    # ── SHFE Gold LTD ─────────────────────────────────────────────────────────
    for ds, contract in [
        ("2026-01-15", "Jan 2026"), ("2026-02-13", "Feb 2026"),
        ("2026-03-13", "Mar 2026"), ("2026-04-15", "Apr 2026"),
        ("2026-05-15", "May 2026"), ("2026-06-15", "Jun 2026"),
        ("2026-07-15", "Jul 2026"), ("2026-08-14", "Aug 2026"),
        ("2026-09-15", "Sep 2026"), ("2026-10-15", "Oct 2026"),
        ("2026-11-13", "Nov 2026"), ("2026-12-15", "Dec 2026"),
    ]:
        events.append({
            "date": ds, "event_type": "shfe_gold",
            "label": f"SHFE Gold {contract} Last Trading Day",
            "noise_assets": ["gold"], "noise_level": "medium",
            "notes": "Shanghai Futures Exchange gold LTD. Overlap with COMEX roll = max noise week.",
        })

    # ── US CPI ────────────────────────────────────────────────────────────────
    for ds, ref in [
        ("2026-01-13", "December 2025"), ("2026-02-13", "January 2026"),
        ("2026-03-11", "February 2026"), ("2026-04-10", "March 2026"),
        ("2026-05-12", "April 2026"),    ("2026-06-10", "May 2026"),
        ("2026-07-14", "June 2026"),     ("2026-08-12", "July 2026"),
        ("2026-09-11", "August 2026"),   ("2026-10-14", "September 2026"),
        ("2026-11-10", "October 2026"),  ("2026-12-10", "November 2026"),
    ]:
        events.append({
            "date": ds, "event_type": "us_cpi", "reference_month": ref,
            "label": f"US CPI — {ref} data (8:30 AM ET / ~18:30 IST)",
            "noise_assets": ["gold", "usdinr"], "noise_level": "high",
            "notes": "Hot CPI → USD up → gold down. Check before treating gold move as war signal.",
            "confirmed": True,
        })

    # ── US PPI ────────────────────────────────────────────────────────────────
    for ds, ref, confirmed in [
        ("2026-01-14", "December 2025", True),  ("2026-02-27", "January 2026", True),
        ("2026-03-18", "February 2026", True),  ("2026-04-14", "March 2026", True),
        ("2026-05-14", "April 2026",    False), ("2026-06-12", "May 2026",    False),
        ("2026-07-16", "June 2026",     False), ("2026-08-14", "July 2026",   False),
        ("2026-09-15", "August 2026",   False), ("2026-10-15", "September 2026", False),
        ("2026-11-13", "October 2026",  False), ("2026-12-11", "November 2026",  False),
    ]:
        conf_note = "" if confirmed else " (date estimated)"
        events.append({
            "date": ds, "event_type": "us_ppi", "reference_month": ref,
            "label": f"US PPI — {ref} data{conf_note} (8:30 AM ET / ~18:30 IST)",
            "noise_assets": ["gold", "usdinr"], "noise_level": "medium",
            "notes": "PPI release — typically 1-4 days after CPI. Amplifies or reverses CPI-driven gold moves.",
            "confirmed": confirmed,
        })

    # ── US NFP (Non-Farm Payrolls) ────────────────────────────────────────────
    # Source: US Bureau of Labor Statistics (BLS) — Employment Situation report
    # Released 8:30 AM ET on the first Friday of the month (occasionally 2nd Fri
    # when the 1st Fri falls on or immediately after a major holiday).
    # Jan–Apr 2026 dates confirmed; May–Dec estimated from first-Friday rule.
    for ds, ref, confirmed in [
        ("2026-01-09", "December 2025",   True),
        ("2026-02-06", "January 2026",    True),
        ("2026-03-06", "February 2026",   True),
        ("2026-04-03", "March 2026",      True),
        ("2026-05-08", "April 2026",      False),  # May 1 = Fri but BLS skips; May 8 estimated
        ("2026-06-05", "May 2026",        False),
        ("2026-07-10", "June 2026",       False),  # Jul 3 = Fri but pre-Independence Day; Jul 10 estimated
        ("2026-08-07", "July 2026",       False),
        ("2026-09-04", "August 2026",     False),
        ("2026-10-02", "September 2026",  False),
        ("2026-11-06", "October 2026",    False),
        ("2026-12-04", "November 2026",   False),
    ]:
        conf_note = "" if confirmed else " (date estimated)"
        events.append({
            "date": ds, "event_type": "us_nfp", "reference_month": ref,
            "label": f"US NFP — {ref} data{conf_note} (8:30 AM ET / ~18:30 IST)",
            "noise_assets": ["gold", "usdinr", "dxy"], "noise_level": "high",
            "notes": (
                "BLS Employment Situation — Non-Farm Payrolls. "
                "Strong jobs → USD up → gold down → looks like ceasefire signal but isn't. "
                "Weak jobs → risk-off → gold up, Nifty down. Always check NFP before reading gold/INR moves."
            ),
            "confirmed": confirmed,
        })

    # ── ADP Employment Report ─────────────────────────────────────────────────
    # Source: ADP / Moody's Analytics — private-sector payrolls estimate
    # Released 8:15 AM ET on Wednesday of NFP week (2 days before NFP Friday).
    # Lower accuracy than NFP but heavily traded. Dates derived from NFP schedule above.
    for ds, ref, confirmed in [
        ("2026-01-07", "December 2025",   True),
        ("2026-02-04", "January 2026",    True),
        ("2026-03-04", "February 2026",   True),
        ("2026-04-01", "March 2026",      True),
        ("2026-05-06", "April 2026",      False),
        ("2026-06-03", "May 2026",        False),
        ("2026-07-08", "June 2026",       False),
        ("2026-08-05", "July 2026",       False),
        ("2026-09-02", "August 2026",     False),
        ("2026-09-30", "September 2026",  False),  # NFP Oct 2 → ADP Wed Sep 30
        ("2026-11-04", "October 2026",    False),
        ("2026-12-02", "November 2026",   False),
    ]:
        conf_note = "" if confirmed else " (date estimated)"
        events.append({
            "date": ds, "event_type": "us_adp", "reference_month": ref,
            "label": f"US ADP Employment — {ref} data{conf_note} (8:15 AM ET / ~17:45 IST)",
            "noise_assets": ["gold", "usdinr", "dxy"], "noise_level": "medium",
            "notes": (
                "ADP private-sector payrolls — released 2 days before NFP. "
                "Often diverges from NFP; treat as directional signal only. "
                "Big surprise → pre-NFP gold/INR move that may not hold after Friday's print."
            ),
            "confirmed": confirmed,
        })

    # ── RBI MPC Policy Meetings 2026 ─────────────────────────────────────────
    # Source: Reserve Bank of India — Monetary Policy Committee
    # Bi-monthly 3-day meetings; rate decision announced on day 3 (~10:00 AM IST).
    # Feb + Apr confirmed; Jun–Dec estimated (bi-monthly pattern).
    # Decision moves: INR, Nifty, Nifty Bank, bond yields, gold (via INR).
    for ds, meeting, confirmed in [
        ("2026-02-07", "Feb 5–7 MPC",  True),   # 25bps cut announced → 6.25%
        ("2026-04-09", "Apr 7–9 MPC",  True),
        ("2026-06-06", "Jun 4–6 MPC",  False),
        ("2026-08-07", "Aug 5–7 MPC",  False),
        ("2026-10-09", "Oct 7–9 MPC",  False),
        ("2026-12-05", "Dec 3–5 MPC",  False),
    ]:
        conf_note = "" if confirmed else " (date estimated)"
        events.append({
            "date": ds, "event_type": "rbi_mpc", "reference_month": meeting,
            "label": f"RBI MPC Decision — {meeting}{conf_note} (~10:00 AM IST)",
            "noise_assets": ["usdinr", "nifty50"], "noise_level": "high",
            "notes": (
                "RBI rate decision — moves INR, Nifty Bank, and bond yields. "
                "Rate cut → INR weakens slightly, Nifty Bank rallies. "
                "Surprise hold/hike → INR strengthens, Nifty Bank sells off. "
                "During war: INR move on MPC day is policy noise, not Hormuz signal."
            ),
            "confirmed": confirmed,
        })

    # ── India CPI (MoSPI) ────────────────────────────────────────────────────
    # Source: Ministry of Statistics & Programme Implementation (MoSPI)
    # Released ~12th–14th of month for prior month's data, ~5:30 PM IST.
    # Jan–Mar confirmed (already released); Apr–Dec estimated.
    # Hot India CPI → RBI less likely to cut → INR firms, rate-sensitive sectors sell off.
    for ds, ref, confirmed in [
        ("2026-01-13", "December 2025", True),
        ("2026-02-12", "January 2026",  True),
        ("2026-03-12", "February 2026", True),
        ("2026-04-14", "March 2026",    False),
        ("2026-05-13", "April 2026",    False),
        ("2026-06-12", "May 2026",      False),
        ("2026-07-14", "June 2026",     False),
        ("2026-08-13", "July 2026",     False),
        ("2026-09-12", "August 2026",   False),
        ("2026-10-13", "September 2026",False),
        ("2026-11-12", "October 2026",  False),
        ("2026-12-14", "November 2026", False),
    ]:
        conf_note = "" if confirmed else " (date estimated)"
        events.append({
            "date": ds, "event_type": "india_cpi", "reference_month": ref,
            "label": f"India CPI — {ref} data{conf_note} (~5:30 PM IST)",
            "noise_assets": ["usdinr", "nifty50"], "noise_level": "medium",
            "notes": (
                "MoSPI Consumer Price Index. Hot print → RBI rate cut odds fall → "
                "INR firms, rate-sensitive sectors (banks, realty) sell off. "
                "During war: INR move on India CPI day is domestic macro, not Hormuz."
            ),
            "confirmed": confirmed,
        })

    # ── India WPI (DPIIT) ────────────────────────────────────────────────────
    # Source: Department for Promotion of Industry and Internal Trade (DPIIT)
    # Released ~14th–16th of month for prior month's data (~12:00 PM IST).
    # Jan–Mar confirmed; Apr–Dec estimated.
    # WPI leads CPI by ~1–2 months; high WPI → inflation pipeline building.
    for ds, ref, confirmed in [
        ("2026-01-14", "December 2025", True),
        ("2026-02-16", "January 2026",  True),
        ("2026-03-16", "February 2026", True),
        ("2026-04-15", "March 2026",    False),
        ("2026-05-14", "April 2026",    False),
        ("2026-06-16", "May 2026",      False),
        ("2026-07-15", "June 2026",     False),
        ("2026-08-14", "July 2026",     False),
        ("2026-09-15", "August 2026",   False),
        ("2026-10-15", "September 2026",False),
        ("2026-11-17", "October 2026",  False),
        ("2026-12-16", "November 2026", False),
    ]:
        conf_note = "" if confirmed else " (date estimated)"
        events.append({
            "date": ds, "event_type": "india_wpi", "reference_month": ref,
            "label": f"India WPI — {ref} data{conf_note} (~12:00 PM IST)",
            "noise_assets": ["usdinr", "nifty50"], "noise_level": "low",
            "notes": (
                "DPIIT Wholesale Price Index — leads CPI by 1-2 months. "
                "War context: oil spike → WPI jumps sharply (fuel + manufacturing inputs). "
                "High WPI during war is expected and does not change RBI stance independently."
            ),
            "confirmed": confirmed,
        })

    # ── ECB Rate Decisions 2026 ───────────────────────────────────────────────
    # Source: ECB published Governing Council meeting calendar
    # Announcement: Thursday 14:15 CET / ~18:45 IST (press conference 14:45 CET)
    # Impact: Biggest central bank after Fed — moves EUR/USD (DXY), gold, global risk sentiment
    for ds, confirmed in [
        ("2026-01-30", True),   # past
        ("2026-03-06", True),   # past
        ("2026-04-17", True),
        ("2026-06-05", True),
        ("2026-07-24", True),
        ("2026-09-11", True),
        ("2026-10-30", True),
        ("2026-12-11", True),
    ]:
        events.append({
            "date": ds,
            "event_type": "ecb_rate_decision",
            "label": f"ECB Rate Decision — {ds} (14:15 CET / ~18:45 IST)",
            "noise_assets": ["gold", "dxy", "usdinr", "nifty"],
            "noise_level": "high",
            "notes": (
                "ECB Governing Council rate decision — second biggest central bank after Fed. "
                "EUR/USD moves sharply on surprise cuts/hikes → DXY spikes/falls → gold reacts inversely. "
                "War context: ECB may cut faster if European energy crisis deepens (Hormuz → LNG shortage). "
                "A surprise ECB cut weakens EUR → strengthens USD → gold pressure, USDINR up. "
                "FII flows to India sensitive to global risk-off triggered by ECB surprises."
            ),
            "confirmed": confirmed,
            "reference_month": None,
        })

    # ── NSE Trading Holidays 2026 ─────────────────────────────────────────────
    # Source: NSE India official holiday list (published annually).
    # Fixed-date national holidays are confirmed; floating (lunar) dates are
    # estimated from 2026 calendar and marked confirmed=False.
    # Significance: NSE closed → Nifty50/IndiaVIX will be null in parquet —
    # do NOT treat null Nifty as a data error on these dates.
    # Only confirmed, fixed-date holidays — no floating/lunar estimates.
    # Add remaining holidays manually when NSE publishes the official list.
    nse_holidays = [
        # date,         label,                confirmed
        ("2026-01-26", "Republic Day",         True),
        ("2026-03-19", "Holi (Dhuleti)",       True),  # confirmed — Nifty null in data
        ("2026-03-31", "Mahavir Jayanti",      True),  # confirmed — Nifty null in data
        ("2026-05-01", "Maharashtra Day",      True),  # NSE-specific; fixed annual
        ("2026-08-15", "Independence Day",     True),  # Sat — NSE already closed weekends
        ("2026-10-02", "Gandhi Jayanti",       True),
        ("2026-12-25", "Christmas",            True),
    ]
    for ds, label, confirmed in nse_holidays:
        conf_note = "" if confirmed else " (estimated)"
        events.append({
            "date": ds,
            "event_type": "nse_holiday",
            "label": f"NSE Holiday — {label}{conf_note}",
            "noise_assets": ["nifty50", "indiavix"],
            "noise_level": "high",
            "notes": (
                f"NSE closed for {label}. Nifty50 and IndiaVIX will be null in market cache. "
                "A missing Nifty value on this date is expected — not a data error or ceasefire signal."
            ),
            "confirmed": confirmed,
        })

    # ── LBMA Bank Holidays 2026 ───────────────────────────────────────────────
    # Source: UK Government — England and Wales bank holiday schedule.
    # All 8 dates confirmed (fixed or formula-derived from Easter 2026 = Apr 5).
    # Significance: LBMA closed → London Gold AM/PM Fix does NOT run.
    # Gold price discovery shifts entirely to COMEX + SHFE on these days.
    # An unusual gold move on an LBMA holiday is COMEX-driven noise, not a war signal.
    lbma_holidays = [
        # date,         label
        ("2026-01-01", "New Year's Day"),
        ("2026-04-03", "Good Friday"),           # Easter Apr 5 → Good Friday Apr 3
        ("2026-04-06", "Easter Monday"),          # Easter Apr 5 → Monday Apr 6
        ("2026-05-04", "Early May Bank Holiday"), # First Monday of May
        ("2026-05-25", "Spring Bank Holiday"),    # Last Monday of May
        ("2026-08-31", "Summer Bank Holiday"),    # Last Monday of August
        ("2026-12-25", "Christmas Day"),
        ("2026-12-28", "Boxing Day (substitute)"),# Dec 26 = Sat → substitute Mon Dec 28
    ]
    for ds, label in lbma_holidays:
        events.append({
            "date": ds,
            "event_type": "lbma_holiday",
            "label": f"LBMA Holiday — {label} (London closed)",
            "noise_assets": ["gold"],
            "noise_level": "medium",
            "notes": (
                f"LBMA closed for {label} (England & Wales bank holiday). "
                "London Gold AM/PM Fix does not run. Gold price discovery shifts to COMEX + SHFE. "
                "Unusual gold moves on this date are exchange-driven noise, not a ceasefire signal."
            ),
            "confirmed": True,
        })

    # ── Upsert all events in a single transaction ─────────────────────────────
    seeded = 0
    updated = 0
    with db_conn() as conn:
        for event in events:
            if _upsert_calendar_event(conn, event):
                seeded += 1
            else:
                updated += 1
        total = conn.execute("SELECT COUNT(*) FROM calendar").fetchone()[0]
    return {"seeded": seeded, "updated": updated, "total_in_db": total}


# ── FII/DII helpers ───────────────────────────────────────────────────────────

def load_fii_dii_history() -> list:
    """Return all FII/DII entries sorted by date (oldest first), nested format."""
    with db_conn() as conn:
        rows = [_FiiDiiRow(*r) for r in conn.execute(
            "SELECT date, fii_buy, fii_sell, fii_net, dii_buy, dii_sell, dii_net "
            "FROM fii_dii ORDER BY date_iso ASC"
        ).fetchall()]

    return [
        {
            "date": r.date,
            "fii": {"buy": r.fii_buy, "sell": r.fii_sell, "net": r.fii_net},
            "dii": {"buy": r.dii_buy, "sell": r.dii_sell, "net": r.dii_net},
        }
        for r in rows
    ]


def upsert_fii_dii_entry(entry: dict) -> bool:
    """
    Insert a FII/DII entry keyed on date. Skips if date already recorded.
    Returns True if a new record was inserted, False if skipped.

    Accepts nested format: {'date': 'DD-Mon-YYYY', 'fii': {'buy', 'sell', 'net'}, 'dii': {...}}
    """
    date_key = entry.get("date", "")
    if not date_key:
        return False
    fii = entry.get("fii") or {}
    dii = entry.get("dii") or {}

    with db_conn() as conn:
        existing = conn.execute(
            "SELECT 1 FROM fii_dii WHERE date = ?", [date_key]
        ).fetchone()
        if existing:
            return False
        from datetime import datetime as _dt_upsert
        try:
            date_iso = _dt_upsert.strptime(date_key, "%d-%b-%Y").strftime("%Y-%m-%d")
        except ValueError:
            date_iso = None
        conn.execute(
            "INSERT INTO fii_dii (date, fii_buy, fii_sell, fii_net, dii_buy, dii_sell, dii_net, date_iso) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                date_key,
                fii.get("buy"), fii.get("sell"), fii.get("net"),
                dii.get("buy"), dii.get("sell"), dii.get("net"),
                date_iso,
            ],
        )
    return True


def get_fii_dii_for_date(nse_date: str) -> dict | None:
    """
    Return a single FII/DII record for the given NSE-format date (DD-Mon-YYYY),
    in nested format {'date', 'fii': {'buy', 'sell', 'net'}, 'dii': {...}}, or None.
    """
    with db_conn() as conn:
        raw = conn.execute(
            "SELECT date, fii_buy, fii_sell, fii_net, dii_buy, dii_sell, dii_net "
            "FROM fii_dii WHERE date = ?",
            [nse_date],
        ).fetchone()
    if raw is None:
        return None
    r = _FiiDiiRow(*raw)
    return {
        "date": r.date,
        "fii": {"buy": r.fii_buy, "sell": r.fii_sell, "net": r.fii_net},
        "dii": {"buy": r.dii_buy, "sell": r.dii_sell, "net": r.dii_net},
    }
