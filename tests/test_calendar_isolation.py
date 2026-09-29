"""Calendar EventKit calls run in a fresh child process (task adf83977)."""
import json
import subprocess

import pytest

from src.tools import calendar as cal


class _FakeProc:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout, self.stderr, self.returncode = stdout, stderr, returncode


def _patch_run(monkeypatch, proc=None, exc=None):
    def fake_run(*a, **k):
        if exc:
            raise exc
        return proc
    monkeypatch.setattr(cal.subprocess, "run", fake_run)


def test_worker_error_type_is_reraised(monkeypatch):
    reply = json.dumps({"ok": False, "error_type": "ValueError", "error": "Calendar not found: x"})
    _patch_run(monkeypatch, _FakeProc(stdout="noise\n" + reply + "\n"))
    with pytest.raises(ValueError, match="Calendar not found: x"):
        cal._run_isolated("list_events", start_date="2026-10-01", end_date="2026-10-01")


def test_unknown_worker_error_type_becomes_runtimeerror(monkeypatch):
    reply = json.dumps({"ok": False, "error_type": "SomethingElse", "error": "boom"})
    _patch_run(monkeypatch, _FakeProc(stdout=reply))
    with pytest.raises(RuntimeError, match="boom"):
        cal._run_isolated("add_event", title="t", start_date="2026-10-01")


def test_worker_without_result_reports_stderr(monkeypatch):
    _patch_run(monkeypatch, _FakeProc(stdout="", stderr="Traceback ... ImportError", returncode=1))
    with pytest.raises(RuntimeError, match="no result.*ImportError"):
        cal._run_isolated("list_events")


def test_worker_timeout_is_a_runtimeerror(monkeypatch):
    _patch_run(monkeypatch, exc=subprocess.TimeoutExpired(cmd="x", timeout=1))
    with pytest.raises(RuntimeError, match="timed out"):
        cal._run_isolated("list_events")


def test_public_handlers_dispatch_to_isolated_worker(monkeypatch):
    seen = []
    monkeypatch.setattr(cal, "_run_isolated", lambda op, **kw: seen.append((op, kw)) or "ok")
    cal.handle_list_events("2026-10-01", "2026-10-02", calendar="market-watch")
    cal.handle_add_event("t", "2026-10-01T10:00:00", calendar="market-watch")
    cal.handle_delete_event("t", calendar="market-watch")
    assert [op for op, _ in seen] == ["list_events", "add_event", "delete_event"]
    assert seen[0][1]["calendar"] == "market-watch"


def test_list_events_raises_on_unknown_calendar(monkeypatch):
    class Store:
        def calendarsForEntityType_(self, _):
            return []
    monkeypatch.setattr(cal, "_store", lambda: Store())
    with pytest.raises(ValueError, match="Calendar not found: nope"):
        cal._list_events_eventkit("2026-10-01T00:00:00Z", "2026-10-02T23:59:00Z", "nope")


def test_unknown_op_in_worker_is_reported(monkeypatch, capsys):
    monkeypatch.setattr(cal.sys, "stdin", type("S", (), {"read": lambda self: "{}"})())
    cal._worker_main(["bogus"])
    reply = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert reply == {"ok": False, "error_type": "ValueError", "error": "Unknown calendar worker op: bogus"}
