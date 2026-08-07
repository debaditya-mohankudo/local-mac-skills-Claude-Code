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
from collections import deque
from typing import Callable

from config import config as cfg

_DB_PATH = cfg.tool_hints_db

# In-memory, per-server-process record of the most recent tool calls this
# session has made: [(call_name, monotonic_ts, found), ...], oldest first.
# Bounded FIFO rather than an unbounded list — full history is already
# persisted to mcp_tool_calls, so this only needs to cover the gate lookback
# window, not the whole process lifetime.
# `found` is None for calls with no result-quality check (see _FOUND_CHECKS);
# True/False for calls that do, e.g. contacts__search actually finding someone.
_SESSION_CALLS_MAXLEN = 100
_SESSION_CALLS: deque[tuple[str, float, bool | None]] = deque(maxlen=_SESSION_CALLS_MAXLEN)

# Gate prereqs stay valid for this many seconds, matching claude-hooks'
# gate_rules.yaml DEFAULT_WINDOW_S — kept even though calls are now persisted
# and technically queryable indefinitely, so "recently looked up" still means
# recently, not "at any point since the process started" (user confirmed).
_GATE_WINDOW_S = 120.0

# Args that may carry personal data — logged as a prefix + length, never
# verbatim, per this repo's privacy rules.
_TRUNCATE_KEYS: dict[tuple[str, str], list[str]] = {
    ("mail", "compose"): ["body"],
    ("imessage", "send"): ["text"],
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


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
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
            ts          TIMESTAMP DEFAULT (datetime('now'))
        )
    """)
    return conn


def _log_call(domain: str, action: str, kwargs: dict, *, ok: bool, error: str | None,
              duration_ms: int, blocked: bool = False, reason: str | None = None) -> None:
    try:
        conn = _connect()
        conn.execute(
            "INSERT INTO mcp_tool_calls "
            "(domain, action, args_json, ok, error, blocked, reason, duration_ms) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (domain, action, json.dumps(_redact(domain, action, kwargs)),
             int(ok), error, int(blocked), reason, duration_ms),
        )
        conn.commit()
        conn.close()
    except Exception:
        # Logging must never break a tool call.
        pass


def _contacts_search_found(kwargs: dict, result: object) -> bool:
    """False when contacts__search's own result string says it found nobody."""
    if not isinstance(result, str):
        return bool(result)
    return "no contacts found" not in result.lower()


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


def _called_recently(call_name: str, window_s: float = _GATE_WINDOW_S) -> bool:
    cutoff = time.monotonic() - window_s
    return any(name == call_name and ts >= cutoff for name, ts, _found in _SESSION_CALLS)


def _last_found(call_name: str, window_s: float = _GATE_WINDOW_S) -> bool | None:
    """`found` of the most recent matching call within the window, or None if
    no such call happened (caller should treat that as "not satisfied")."""
    cutoff = time.monotonic() - window_s
    result: bool | None = None
    for name, ts, found in _SESSION_CALLS:
        if name == call_name and ts >= cutoff:
            result = found
    return result


def _vault_guard(domain: str, action: str, kwargs: dict) -> None:
    if domain != "vault" or action not in ("write", "append", "delete", "move"):
        return
    from tools.vault import _vault_path, VAULT_PATH

    vault_root = VAULT_PATH.resolve()
    for key in ("path", "to"):
        if key not in kwargs:
            continue
        resolved = _vault_path(kwargs[key]).resolve()
        if resolved != vault_root and vault_root not in resolved.parents:
            raise PermissionError(
                f"Refused: vault__{action} {key}={kwargs[key]!r} resolves outside the vault"
            )


def _imessage_guard(domain: str, action: str, kwargs: dict) -> None:
    if domain != "imessage" or action != "send":
        return
    found = _last_found("contacts__search")
    if found is None:
        raise PermissionError(
            f"Refused: imessage__send requires contacts__search within the last "
            f"{int(_GATE_WINDOW_S)}s. Call contacts__search first, then retry."
        )
    if found is False:
        raise PermissionError(
            "Refused: imessage__send — the most recent contacts__search within "
            f"the last {int(_GATE_WINDOW_S)}s found no matching contact. "
            "Confirm the recipient before sending, or search again with the right name."
        )


def _mail_guard(domain: str, action: str, kwargs: dict) -> None:
    if domain == "mail" and action == "delete" and not _called_recently("mail__read"):
        raise PermissionError(
            f"Refused: mail__delete requires mail__read within the last "
            f"{int(_GATE_WINDOW_S)}s. Call mail__read first, then retry."
        )


_PRECHECKS = (_vault_guard, _imessage_guard, _mail_guard)


@contextlib.contextmanager
def tool_called(domain: str, action: str, kwargs: dict):
    """Wrap one dispatcher call: pre-check gates, then log on exit.

    Raises PermissionError (and logs blocked=1) if a pre-check refuses the
    call. Otherwise yields a single-key holder dict the caller must set
    holder["result"] on after calling the handler — that's how a later gate
    (e.g. imessage__send needing contacts__search to have found someone) gets
    to see the handler's return value, not just that it was called. Logs the
    outcome and — only on success — records the call (with its `found`
    quality flag) in the in-memory session list.
    """
    call_name = f"{domain}__{action}"

    for check in _PRECHECKS:
        try:
            check(domain, action, kwargs)
        except PermissionError as exc:
            _log_call(domain, action, kwargs, ok=False, error=str(exc),
                       duration_ms=0, blocked=True, reason=str(exc))
            raise

    start = time.monotonic()
    error: str | None = None
    holder: dict = {}
    try:
        yield holder
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        _log_call(domain, action, kwargs, ok=error is None, error=error, duration_ms=duration_ms)
        if error is None:
            found = _found(domain, action, kwargs, holder.get("result"))
            _SESSION_CALLS.append((call_name, time.monotonic(), found))
