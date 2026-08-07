"""
podcasts.py
-----------
MCP tool handlers for Podcasts.app, ported from
local-mac-tool/Sources/LocalMacMCP/PodcastsTool.swift — pure sqlite3 read
against Podcasts.app's local library DB, no AppleScript involved at all
(same as Swift's own implementation; grooming's speculation about needing
an AppleScript-dictionary fallback was moot, the Swift tool never used one).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

_DB = (
    Path.home()
    / "Library"
    / "Group Containers"
    / "243LU875E5.groups.com.apple.podcasts"
    / "Documents"
    / "MTLibrary.sqlite"
)

# Core Data timestamps are seconds since 2001-01-01 (Apple's NSDate epoch)
_APPLE_EPOCH_OFFSET = 978307200


def _core_data_ts_to_iso(ts) -> str | None:
    if ts is None or ts <= 0:
        return None
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts + _APPLE_EPOCH_OFFSET, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _seconds_to_hms(s: float) -> str:
    total = int(s)
    h, rem = divmod(total, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h > 0 else f"{m}:{sec:02d}"


def _conn():
    return sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)


def _episode_dict(row: dict) -> dict:
    d = {}
    if row.get("ZTITLE") is not None:
        d["title"] = row["ZTITLE"]
    if row.get("ZUUID") is not None:
        d["uuid"] = row["ZUUID"]
    if row.get("ZDURATION"):
        d["duration"] = _seconds_to_hms(row["ZDURATION"])
    if row.get("ZPLAYHEAD"):
        d["playhead"] = _seconds_to_hms(row["ZPLAYHEAD"])
    if row.get("ZHASBEENPLAYED") is not None:
        d["played"] = row["ZHASBEENPLAYED"] == 1
    if row.get("ZISNEW") is not None:
        d["is_new"] = row["ZISNEW"] == 1
    if row.get("ZSAVED") is not None:
        d["saved"] = row["ZSAVED"] == 1
    if row.get("ZPUBDATE") is not None:
        d["published"] = _core_data_ts_to_iso(row["ZPUBDATE"]) or row["ZPUBDATE"]
    if row.get("ZENCLOSUREURL") is not None:
        d["audio_url"] = row["ZENCLOSUREURL"]
    return d


def handle_list() -> list:
    """List all subscribed podcasts with episode counts."""
    con = _conn()
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            """
            SELECT ZTITLE, ZAUTHOR, ZNEWEPISODESCOUNT, ZLIBRARYEPISODESCOUNT,
                   ZDOWNLOADEDEPISODESCOUNT, ZSUBSCRIBED, ZUUID
            FROM ZMTPODCAST
            ORDER BY ZTITLE ASC
            """
        ).fetchall()
    finally:
        con.close()

    result = []
    for r in rows:
        d = {}
        if r["ZTITLE"] is not None:
            d["title"] = r["ZTITLE"]
        if r["ZAUTHOR"] is not None:
            d["author"] = r["ZAUTHOR"]
        if r["ZNEWEPISODESCOUNT"] is not None:
            d["new_episodes"] = r["ZNEWEPISODESCOUNT"]
        if r["ZLIBRARYEPISODESCOUNT"] is not None:
            d["library_episodes"] = r["ZLIBRARYEPISODESCOUNT"]
        if r["ZDOWNLOADEDEPISODESCOUNT"] is not None:
            d["downloaded"] = r["ZDOWNLOADEDEPISODESCOUNT"]
        if r["ZSUBSCRIBED"] is not None:
            d["subscribed"] = r["ZSUBSCRIBED"] == 1
        if r["ZUUID"] is not None:
            d["uuid"] = r["ZUUID"]
        result.append(d)
    return result


def handle_episodes(podcast_title: str = "", podcast_uuid: str = "", limit: int = 20, unplayed: bool = False) -> list:
    """List episodes for a podcast. Provide podcast_title (partial match) or podcast_uuid."""
    con = _conn()
    con.row_factory = sqlite3.Row
    try:
        if podcast_uuid:
            resolved_uuid = podcast_uuid
        elif podcast_title:
            match = con.execute(
                "SELECT ZUUID FROM ZMTPODCAST WHERE ZTITLE LIKE ? LIMIT 1",
                (f"%{podcast_title}%",),
            ).fetchone()
            if not match:
                raise ValueError(f"No podcast found matching: {podcast_title}")
            resolved_uuid = match["ZUUID"]
        else:
            raise ValueError("Provide podcast_title or podcast_uuid")

        unplayed_filter = "AND e.ZHASBEENPLAYED = 0 AND e.ZMARKASPLAYED = 0" if unplayed else ""
        rows = con.execute(
            f"""
            SELECT e.ZTITLE, e.ZDURATION, e.ZPLAYHEAD, e.ZHASBEENPLAYED,
                   e.ZISNEW, e.ZSAVED, e.ZPUBDATE, e.ZUUID, e.ZENCLOSUREURL
            FROM ZMTEPISODE e
            WHERE e.ZPODCASTUUID = ?
            AND e.ZISHIDDEN = 0
            {unplayed_filter}
            ORDER BY e.ZPUBDATE DESC
            LIMIT ?
            """,
            (resolved_uuid, limit),
        ).fetchall()
    finally:
        con.close()
    return [_episode_dict(dict(r)) for r in rows]


def handle_recent(limit: int = 20, new_only: bool = False) -> list:
    """List recent episodes across all podcasts. Set new_only=True for unheard episodes."""
    new_filter = "AND e.ZISNEW = 1" if new_only else ""
    con = _conn()
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            f"""
            SELECT e.ZTITLE, e.ZDURATION, e.ZPLAYHEAD, e.ZHASBEENPLAYED,
                   e.ZISNEW, e.ZSAVED, e.ZPUBDATE, e.ZUUID,
                   p.ZTITLE as podcast_title
            FROM ZMTEPISODE e
            LEFT JOIN ZMTPODCAST p ON e.ZPODCASTUUID = p.ZUUID
            WHERE e.ZISHIDDEN = 0
            {new_filter}
            ORDER BY e.ZPUBDATE DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        con.close()

    result = []
    for r in rows:
        d = _episode_dict(dict(r))
        if r["podcast_title"] is not None:
            d["podcast"] = r["podcast_title"]
        result.append(d)
    return result


def handle_in_progress() -> list:
    """List episodes that have been started but not finished (have a playhead position)."""
    con = _conn()
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            """
            SELECT e.ZTITLE, e.ZDURATION, e.ZPLAYHEAD, e.ZHASBEENPLAYED,
                   e.ZISNEW, e.ZSAVED, e.ZPUBDATE, e.ZUUID,
                   p.ZTITLE as podcast_title
            FROM ZMTEPISODE e
            LEFT JOIN ZMTPODCAST p ON e.ZPODCASTUUID = p.ZUUID
            WHERE e.ZISHIDDEN = 0
            AND e.ZPLAYHEAD > 0
            AND e.ZHASBEENPLAYED = 0
            ORDER BY e.ZLASTDATEPLAYED DESC
            LIMIT 20
            """
        ).fetchall()
    finally:
        con.close()

    result = []
    for r in rows:
        d = _episode_dict(dict(r))
        if r["podcast_title"] is not None:
            d["podcast"] = r["podcast_title"]
        result.append(d)
    return result
