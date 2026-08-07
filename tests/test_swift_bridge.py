"""Tests for src/swift_bridge.py — subprocess wrapping and error handling."""
import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from swift_bridge import call_swift


def _mock_result(stdout: bytes, returncode: int = 0, stderr: bytes = b"") -> MagicMock:
    m = MagicMock(spec=subprocess.CompletedProcess)
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


class TestCallSwift:
    def test_returns_data_on_success(self):
        payload = json.dumps({"status": "ok", "data": {"key": "val"}}).encode()
        with patch("swift_bridge.subprocess.run", return_value=_mock_result(payload)):
            result = call_swift("some-command")
        assert result == {"key": "val"}

    def test_raises_on_nonzero_exit(self):
        err = json.dumps({"message": "not found"}).encode()
        with patch("swift_bridge.subprocess.run", return_value=_mock_result(b"", returncode=1, stderr=err)):
            with pytest.raises(RuntimeError, match="not found"):
                call_swift("bad-command")

    def test_raises_on_status_not_ok(self):
        payload = json.dumps({"status": "error", "message": "oops"}).encode()
        with patch("swift_bridge.subprocess.run", return_value=_mock_result(payload)):
            with pytest.raises(RuntimeError, match="oops"):
                call_swift("failing-command")

    def test_raises_plain_stderr_when_not_json(self):
        with patch("swift_bridge.subprocess.run", return_value=_mock_result(b"", returncode=1, stderr=b"binary missing")):
            with pytest.raises(RuntimeError, match="binary missing"):
                call_swift("cmd")

    def test_passes_payload_as_stdin_json(self):
        payload = json.dumps({"status": "ok", "data": None}).encode()
        with patch("swift_bridge.subprocess.run", return_value=_mock_result(payload)) as mock_run:
            call_swift("cmd", {"arg": 1})
        _, kwargs = mock_run.call_args
        assert kwargs["input"] == b'{"arg": 1}'
