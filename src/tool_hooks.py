"""Host-agnostic pre/post hooks around every MCP tool call.

External Claude Code hooks (settings.json PreToolUse/PostToolUse) only fire
when that particular host's hook process is wired up and running. This module
is embedded directly in dispatcher.py:_wrap instead — the one choke point
every domain__action tool call already funnels through — so logging and
blocking pre-checks hold regardless of which host is driving the server.

Mirrors tool_hints.sqlite's existing bash_audit table (same DB, same shape:
ok/error/blocked/reason/ts) one level up, for MCP tool calls instead of Bash
commands.
"""
from __future__ import annotations

import contextlib
import json
import sqlite3
import time
from typing import Callable

from config import config as cfg

_DB_PATH = cfg.tool_hints_db

# Gate prereqs stay valid for this many seconds. Calls are persisted to
# mcp_tool_calls and queryable indefinitely, but "recently looked up" still
# means recently, not "at any point in the log" (user confirmed).
#
# Gates read the persisted table rather than process memory, so a prerequisite
# satisfied by one process (the MCP server, or one `mac` CLI invocation)
# counts for a gated call made by another — each `mac` call is its own process.
_GATE_WINDOW_S = 120.0


class Refused(PermissionError):
    """A policy refusal: a gate, or a handler refusing its own arguments (a
    vault path outside the vault). Logged as blocked. A plain PermissionError
    from the OS (e.g. a macOS privacy denial) is an ordinary error, not this."""

# Args that may carry personal data. A value longer than _TRUNCATE_LEN is
# logged as a prefix + length; a shorter one is logged as is (task:593321f0).
# Each key must be a parameter of that handler, or redaction silently never
# matches — tests/test_tool_hooks_redact.py checks this.
_TRUNCATE_KEYS: dict[tuple[str, str], list[str]] = {
    ("mail", "compose"): ["body"],
    ("imessage", "send"): ["message"],
    ("vault", "write"): ["content"],
    ("vault", "append"): ["content"],
}
_TRUNCATE_LEN = 200


def _redact(domain: str, action: str, kwargs: dict) -> dict:
    keys = _TRUNCATE_KEYS.get((domain, action))
    if not keys:
        return kwargs
    redacted = dict(kwargs)
    for key in keys:
        value = redacted.get(key)
        if isinstance(value, str) and len(value) > _TRUNCATE_LEN:
            redacted[key] = f"{value[:_TRUNCATE_LEN]}... [{len(value)} chars]"
    return redacted


# DB paths whose mcp_tool_calls schema this process has already ensured. Keyed
# by path (not a flag) because tests point _DB_PATH at a scratch file.
_SCHEMA_READY: set[str] = set()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    if str(_DB_PATH) not in _SCHEMA_READY:
        _ensure_schema(conn)
        _SCHEMA_READY.add(str(_DB_PATH))
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mcp_tool_calls (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            domain      TEXT,
            action      TEXT,
            args_json   TEXT,
            ok          INTEGER DEFAULT 1,
            error       TEXT,
            blocked     INTEGER DEFAULT 0,
            reason      TEXT,
            duration_ms INTEGER,
            ts          TIMESTAMP DEFAULT (datetime('now')),
            found       INTEGER
        )
    """)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(mcp_tool_calls)")}
    if "found" not in columns:
        conn.execute("ALTER TABLE mcp_tool_calls ADD COLUMN found INTEGER")


def _log_call(domain: str, action: str, kwargs: dict, *, ok: bool, error: str | None,
              duration_ms: int, blocked: bool = False, reason: str | None = None,
              found: bool | None = None) -> None:
    try:
        conn = _connect()
        conn.execute(
            "INSERT INTO mcp_tool_calls "
            "(domain, action, args_json, ok, error, blocked, reason, duration_ms, found) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (domain, action, json.dumps(_redact(domain, action, kwargs)),
             int(ok), error, int(blocked), reason, duration_ms,
             None if found is None else int(found)),
        )
        conn.commit()
        conn.close()
    except Exception:
        # Logging must never break a tool call. A lost row only means a later
        # gate sees no prerequisite and refuses — the safe direction.
        pass


def _contacts_search_found(kwargs: dict, result: object) -> bool:
    """False when contacts__search found nobody (handle_search returns [])."""
    return bool(result)


# Per-(domain, action) result-quality checks. A call with no entry here has no
# such notion — its `found` is recorded as None and gates that don't care
# about it (e.g. mail__read for the mail__delete gate) are unaffected.
_FOUND_CHECKS: dict[tuple[str, str], Callable[[dict, object], bool]] = {
    ("contacts", "search"): _contacts_search_found,
}


def _found(domain: str, action: str, kwargs: dict, result: object) -> bool | None:
    check = _FOUND_CHECKS.get((domain, action))
    if check is None:
        return None
    try:
        return bool(check(kwargs, result))
    except Exception:
        return None


def _recent_call(call_name: str, window_s: float = _GATE_WINDOW_S) -> tuple[bool, bool | None]:
    """(happened, found) for the most recent successful `call_name` within the
    window, read from mcp_tool_calls. A read failure counts as "not happened",
    so a gate fails closed."""
    domain, _, action = call_name.partition("__")
    try:
        with contextlib.closing(_connect()) as conn:
            row = conn.execute(
                "SELECT found FROM mcp_tool_calls "
                "WHERE domain = ? AND action = ? AND ok = 1 AND blocked = 0 "
                "AND ts >= datetime('now', ?) ORDER BY id DESC LIMIT 1",
                (domain, action, f"-{int(window_s)} seconds"),
            ).fetchone()
    except Exception:
        return False, None
    if row is None:
        return False, None
    return True, None if row[0] is None else bool(row[0])


def _called_recently(call_name: str, window_s: float = _GATE_WINDOW_S) -> bool:
    return _recent_call(call_name, window_s)[0]


def _last_found(call_name: str, window_s: float = _GATE_WINDOW_S) -> bool | None:
    """`found` of the most recent matching call within the window, or None if
    no such call happened (caller should treat that as "not satisfied")."""
    happened, found = _recent_call(call_name, window_s)
    return found if happened else None


def _imessage_guard(domain: str, action: str, kwargs: dict) -> None:
    if domain != "imessage" or action != "send":
        return
    found = _last_found("contacts__search")
    if found is None:
        raise Refused(
            f"Refused: imessage__send requires contacts__search within the last "
            f"{int(_GATE_WINDOW_S)}s. Call contacts__search first, then retry."
        )
    if found is False:
        raise Refused(
            "Refused: imessage__send — the most recent contacts__search within "
            f"the last {int(_GATE_WINDOW_S)}s found no matching contact. "
            "Confirm the recipient before sending, or search again with the right name."
        )


def _mail_guard(domain: str, action: str, kwargs: dict) -> None:
    if domain == "mail" and action == "delete" and not _called_recently("mail__read"):
        raise Refused(
            f"Refused: mail__delete requires mail__read within the last "
            f"{int(_GATE_WINDOW_S)}s. Call mail__read first, then retry."
        )


_PRECHECKS = (_imessage_guard, _mail_guard)


@contextlib.contextmanager
def tool_called(domain: str, action: str, kwargs: dict):
    """Wrap one dispatcher call: pre-check gates, then log on exit.

    Raises Refused (and logs blocked=1) if a pre-check refuses the
    call. Otherwise yields a single-key holder dict the caller must set
    holder["result"] on after calling the handler — that's how a later gate
    (e.g. imessage__send needing contacts__search to have found someone) gets
    to see the handler's return value, not just that it was called. Logs the
    outcome, with its `found` quality flag on success; that row is what later
    gates read.
    """
    for check in _PRECHECKS:
        try:
            check(domain, action, kwargs)
        except Refused as exc:
            _log_call(domain, action, kwargs, ok=False, error=str(exc),
                       duration_ms=0, blocked=True, reason=str(exc))
            raise

    start = time.monotonic()
    error: str | None = None
    # A handler refusing its own arguments (e.g. a vault path that resolves
    # outside the vault, checked in tools.vault._vault_path) is a block too.
    blocked = False
    holder: dict = {}
    try:
        yield holder
    except Exception as exc:
        error = str(exc)
        blocked = isinstance(exc, Refused)
        raise
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        found = _found(domain, action, kwargs, holder.get("result")) if error is None else None
        _log_call(domain, action, kwargs, ok=error is None, error=error, duration_ms=duration_ms,
                  blocked=blocked, reason=error if blocked else None, found=found)
