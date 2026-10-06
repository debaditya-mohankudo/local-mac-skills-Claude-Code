"""Tests for notes.handle_add tagging. AppleScript is mocked."""
from __future__ import annotations

import src.tools.notes as notes


def _patch(monkeypatch, *outputs):
    scripts, outs = [], list(outputs)

    def fake(script):
        scripts.append(script)
        out = outs.pop(0)
        if isinstance(out, Exception):
            raise out
        return out

    monkeypatch.setattr(notes, "_run_applescript", fake)
    return scripts


def test_parse_tags_strips_hash_dedupes_and_drops_junk():
    assert notes._parse_tags("#market-watch, gold  #market-watch bad!tag") == ["market-watch", "gold"]
    assert notes._parse_tags("") == []


def test_no_tags_makes_a_single_osascript_call(monkeypatch):
    scripts = _patch(monkeypatch, "id-1|||T")
    result = notes.handle_add("T", "<div>b</div>")
    assert len(scripts) == 1
    assert "tags" not in result and "tags_error" not in result


def test_tags_are_typed_after_creation(monkeypatch):
    scripts = _patch(monkeypatch, "id-1|||T", "")
    result = notes.handle_add("T", tags="market-watch gold")
    assert result["tags"] == ["market-watch", "gold"]
    typing = scripts[1]
    assert 'show note id "id-1"' in typing
    assert 'keystroke "#market-watch"' in typing and 'keystroke "#gold"' in typing
    assert "refusing to type" in typing


def test_tag_failure_keeps_the_note_and_reports(monkeypatch):
    _patch(monkeypatch, "id-1|||T", RuntimeError("not allowed assistive access"))
    result = notes.handle_add("T", tags="x")
    assert result["status"] == "created"
    assert "assistive" in result["tags_error"]
