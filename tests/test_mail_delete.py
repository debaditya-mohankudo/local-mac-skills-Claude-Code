"""Tests for mail.handle_delete outcome reporting (task:ad9cae1c).

The defect these cover is not that deletion failed — it is that a partial
delete was INDISTINGUISHABLE from a complete one. The old handler counted
successes and echoed back every id it was given, so a caller handed 22 ids and
told "18" could not learn which 4 survived without re-reading the mailbox.

AppleScript is mocked. The behaviour under test is the parsing and the status
decision, not Mail.app.
"""
from __future__ import annotations

import pytest

import src.tools.mail as mail


@pytest.fixture
def configured(monkeypatch):
    """A mail account, so _resolve() does not raise on an unconfigured host."""
    monkeypatch.setattr(mail, "ACCOUNTS", {"gmail": ("UUID-1", "you@example.com")})
    monkeypatch.setattr(mail, "DEFAULT_ACCOUNT", "gmail")


def _mock_applescript(monkeypatch, output: str):
    monkeypatch.setattr(mail, "_run_applescript", lambda script: output)


class TestAllDeleted:
    def test_status_is_deleted_and_ids_are_listed(self, configured, monkeypatch):
        _mock_applescript(monkeypatch, "1=deleted\n2=deleted\n3=deleted\n")
        result = mail.handle_delete([1, 2, 3])
        assert result["status"] == "deleted"
        assert result["deleted_count"] == 3
        assert result["deleted"] == [1, 2, 3]
        assert result["failed"] == []
        assert result["requested"] == 3


class TestPartialFailure:
    """The case the original defect hid."""

    def test_status_is_partial_not_deleted(self, configured, monkeypatch):
        _mock_applescript(monkeypatch, "1=deleted\n2=notfound\n3=deleted\n")
        result = mail.handle_delete([1, 2, 3])
        assert result["status"] == "partial"

    def test_failed_ids_are_named(self, configured, monkeypatch):
        _mock_applescript(monkeypatch, "1=deleted\n2=notfound\n3=deleted\n")
        result = mail.handle_delete([1, 2, 3])
        assert result["deleted"] == [1, 3]
        assert [f["message_id"] for f in result["failed"]] == [2]
        assert result["failed"][0]["reason"] == "notfound"

    def test_counts_reconcile_with_the_request(self, configured, monkeypatch):
        """deleted + failed must account for every id asked about."""
        _mock_applescript(monkeypatch, "1=deleted\n2=notfound\n3=deleted\n")
        result = mail.handle_delete([1, 2, 3])
        assert result["deleted_count"] + len(result["failed"]) == result["requested"]

    def test_applescript_error_is_carried_through(self, configured, monkeypatch):
        _mock_applescript(monkeypatch, "1=deleted\n2=error:Mail got an error: no access\n")
        result = mail.handle_delete([1, 2])
        assert result["status"] == "partial"
        assert "no access" in result["failed"][0]["reason"]


class TestSilenceIsNotSuccess:
    def test_unreported_id_counts_as_failed(self, configured, monkeypatch):
        """An id AppleScript never mentions must not be assumed deleted —
        that silence is exactly what made the original defect invisible."""
        _mock_applescript(monkeypatch, "1=deleted\n")
        result = mail.handle_delete([1, 2, 3])
        assert result["status"] == "partial"
        assert sorted(f["message_id"] for f in result["failed"]) == [2, 3]
        assert all(f["reason"] == "no result returned" for f in result["failed"])

    def test_empty_output_means_nothing_was_deleted(self, configured, monkeypatch):
        _mock_applescript(monkeypatch, "")
        result = mail.handle_delete([1, 2])
        assert result["status"] == "failed"
        assert result["deleted_count"] == 0
        assert len(result["failed"]) == 2


class TestArgumentValidation:
    def test_empty_id_list_is_rejected(self, configured):
        with pytest.raises(ValueError):
            mail.handle_delete([])
