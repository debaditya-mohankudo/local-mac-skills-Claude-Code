"""The imessage send / mail delete gates read the persisted mcp_tool_calls log.

Each `mac` CLI call is its own process, so a prerequisite met in one process
must satisfy the gate in another, and only for _GATE_WINDOW_S seconds.
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

import tool_hooks

SRC = Path(__file__).resolve().parent.parent / "src"


@pytest.fixture
def db(tool_hints_db):
    return tool_hints_db


def _call(domain, action, result, **kwargs):
    with tool_hooks.tool_called(domain, action, kwargs) as holder:
        holder["result"] = result


def _in_other_process(db: Path, domain: str, action: str, result: str) -> None:
    script = (
        "import sys, tool_hooks\n"
        f"tool_hooks._DB_PATH = {str(db)!r}\n"
        f"with tool_hooks.tool_called({domain!r}, {action!r}, {{}}) as h:\n"
        f"    h['result'] = {result}\n"
    )
    subprocess.run([sys.executable, "-c", script], cwd=SRC, check=True,
                   env={"PYTHONPATH": str(SRC), "HOME": str(Path.home())})


def test_send_refused_with_no_search(db):
    with pytest.raises(PermissionError, match="requires contacts__search"):
        _call("imessage", "send", "sent", to="A")


def test_search_in_another_process_satisfies_send(db):
    _in_other_process(db, "contacts", "search", "[{'name': 'A'}]")
    _call("imessage", "send", "sent", to="A")


def test_empty_search_in_another_process_refuses_send(db):
    _in_other_process(db, "contacts", "search", "[]")
    with pytest.raises(PermissionError, match="found no matching contact"):
        _call("imessage", "send", "sent", to="A")


def test_latest_search_wins(db):
    _call("contacts", "search", [], name="wrong")
    _call("contacts", "search", [{"name": "A"}], name="A")
    _call("imessage", "send", "sent", to="A")


def test_mail_read_in_another_process_satisfies_delete(db):
    _in_other_process(db, "mail", "read", "{'emails': []}")
    _call("mail", "delete", {"status": "deleted"}, message_ids=[1])


def test_prerequisite_older_than_window_does_not_count(db):
    _call("mail", "read", {"emails": []})
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE mcp_tool_calls SET ts = datetime('now', ?)",
                     (f"-{int(tool_hooks._GATE_WINDOW_S) + 5} seconds",))
    with pytest.raises(PermissionError, match="requires mail__read"):
        _call("mail", "delete", {}, message_ids=[1])


def test_failed_or_blocked_prerequisite_does_not_count(db):
    with pytest.raises(RuntimeError):
        with tool_hooks.tool_called("mail", "read", {}):
            raise RuntimeError("Mail not running")
    with pytest.raises(PermissionError):
        _call("mail", "delete", {}, message_ids=[1])


def test_unreadable_log_fails_closed(db, monkeypatch):
    _call("contacts", "search", [{"name": "A"}], name="A")
    monkeypatch.setattr(tool_hooks, "_DB_PATH", db.parent / "missing-dir" / "x.sqlite")
    with pytest.raises(PermissionError):
        _call("imessage", "send", "sent", to="A")


def test_found_column_added_to_existing_table(db):
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE mcp_tool_calls (id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT, "
                     "action TEXT, args_json TEXT, ok INTEGER DEFAULT 1, error TEXT, blocked INTEGER "
                     "DEFAULT 0, reason TEXT, duration_ms INTEGER, ts TIMESTAMP DEFAULT (datetime('now')))")
    _call("contacts", "search", [{"name": "A"}], name="A")
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT found FROM mcp_tool_calls").fetchall() == [(1,)]
