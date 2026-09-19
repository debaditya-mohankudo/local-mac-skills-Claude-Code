"""Tests for handle_foundation_models_query — Swift binary path with HTTP fallback."""
from unittest.mock import patch

import pytest

from tools.system import handle_foundation_models_query


def test_uses_swift_binary():
    with patch("swift_bridge.call_swift", return_value="PROXY_OF") as call:
        assert handle_foundation_models_query("classify") == "PROXY_OF"
    cmd, payload = call.call_args.args
    assert cmd == "foundation-models-query"
    assert payload["prompt"] == "classify"


def test_falls_back_to_http_message_when_swift_fails():
    with patch("swift_bridge.call_swift", side_effect=RuntimeError("boom")), \
         patch("urllib.request.urlopen", side_effect=OSError("down")):
        assert "unavailable" in handle_foundation_models_query("x")


def test_empty_prompt_raises():
    with pytest.raises(ValueError):
        handle_foundation_models_query("")
