"""Tests for safari.handle_open. AppleScript is mocked."""
from __future__ import annotations

import src.tools.safari as safari


def _patch(monkeypatch, out=""):
    scripts = []

    def fake(script):
        scripts.append(script)
        return out

    monkeypatch.setattr(safari, "run_osascript", fake)
    monkeypatch.setattr(safari, "_check_allowed", lambda url: True)
    return scripts


def test_default_open_uses_open_location(monkeypatch):
    scripts = _patch(monkeypatch)
    assert safari.handle_open("https://example.com/a") == "Opened: https://example.com/a"
    assert scripts == ['tell application "Safari" to open location "https://example.com/a"']


def test_new_window_makes_a_document_and_activates(monkeypatch):
    scripts = _patch(monkeypatch)
    result = safari.handle_open("https://example.com/a", new_window=True)
    assert result == "Opened in new window: https://example.com/a"
    assert len(scripts) == 1
    assert 'make new document with properties {URL:"https://example.com/a"}' in scripts[0]
    assert "activate" in scripts[0]
    assert "open location" not in scripts[0]


def test_url_quotes_cannot_break_out_of_the_applescript_string(monkeypatch):
    scripts = _patch(monkeypatch)
    safari.handle_open('https://e.com/"&quit', new_window=True)
    safari.handle_open('https://e.com/"&quit')
    assert all('https://e.com/\\"&quit' in s for s in scripts)


def test_blocked_url_never_reaches_osascript(monkeypatch):
    scripts = _patch(monkeypatch)
    monkeypatch.setattr(safari, "_check_allowed", lambda url: False)
    try:
        safari.handle_open("https://blocked.example", new_window=True)
    except safari.LocalProcessError:
        pass
    else:
        raise AssertionError("expected LocalProcessError")
    assert scripts == []
