"""Tests for notes.handle_update.

AppleScript is mocked. The behaviour under test is the branching (not found /
locked / replace / append) and what script gets built, not Notes.app.
"""
from __future__ import annotations

import pytest

import src.tools.notes as notes


class _Recorder:
    """Stand-in for _run_applescript: returns canned output per call, records scripts."""

    def __init__(self, *outputs: str):
        self.outputs = list(outputs)
        self.scripts: list[str] = []

    def __call__(self, script: str) -> str:
        self.scripts.append(script)
        return self.outputs.pop(0)


def _patch(monkeypatch, *outputs: str) -> _Recorder:
    rec = _Recorder(*outputs)
    monkeypatch.setattr(notes, "_run_applescript", rec)
    return rec


class TestGuards:
    def test_bad_mode_is_rejected_without_touching_notes(self, monkeypatch):
        rec = _patch(monkeypatch)
        result = notes.handle_update("id-1", "<div>x</div>", mode="prepend")
        assert "error" in result
        assert rec.scripts == []

    def test_unknown_id_reports_not_found_and_does_not_write(self, monkeypatch):
        rec = _patch(monkeypatch, "NOTFOUND")
        result = notes.handle_update("missing", "<div>x</div>")
        assert result == {"error": "Note not found: missing"}
        assert len(rec.scripts) == 1  # the probe only, no write

    def test_locked_note_is_refused_and_does_not_write(self, monkeypatch):
        rec = _patch(monkeypatch, "LOCKED")
        result = notes.handle_update("id-1", "<div>x</div>")
        assert "locked" in result["error"].lower()
        assert len(rec.scripts) == 1


class TestReplace:
    def test_keeps_existing_title_as_first_line(self, monkeypatch):
        rec = _patch(monkeypatch, "OK|||My Note", "id-1|||My Note")
        result = notes.handle_update("id-1", "<ul><li>new</li></ul>")
        assert result == {"status": "updated", "mode": "replace", "id": "id-1", "title": "My Note"}
        write = rec.scripts[1]
        assert 'set body of n to "<div>My Note</div><ul><li>new</li></ul>"' in write

    def test_explicit_title_overrides_the_existing_one(self, monkeypatch):
        rec = _patch(monkeypatch, "OK|||Old", "id-1|||New")
        notes.handle_update("id-1", "<div>b</div>", title="New")
        assert "<div>New</div><div>b</div>" in rec.scripts[1]

    def test_title_is_html_escaped(self, monkeypatch):
        rec = _patch(monkeypatch, "OK|||S&P <500>", "id-1|||S&P <500>")
        notes.handle_update("id-1", "<div>b</div>")
        assert "<div>S&amp;P &lt;500&gt;</div>" in rec.scripts[1]

    def test_quotes_and_backslashes_in_body_are_escaped_for_applescript(self, monkeypatch):
        rec = _patch(monkeypatch, "OK|||T", "id-1|||T")
        notes.handle_update("id-1", 'say "hi" \\ there')
        assert 'say \\"hi\\" \\\\ there' in rec.scripts[1]


class TestAppend:
    def test_appends_after_existing_body_and_leaves_title_alone(self, monkeypatch):
        rec = _patch(monkeypatch, "OK|||My Note", "id-1|||My Note")
        result = notes.handle_update("id-1", "<div>more</div>", mode="append")
        assert result["mode"] == "append"
        write = rec.scripts[1]
        assert 'set body of n to (body of n) & "<div>more</div>"' in write
        assert "<div>My Note</div>" not in write


@pytest.mark.parametrize("action", ["update"])
def test_update_is_registered_in_the_dispatcher(action):
    from src.dispatcher import DOMAIN_MAP

    assert action in DOMAIN_MAP["notes"][1]
