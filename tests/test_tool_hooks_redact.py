"""Personal-data args are stored in mcp_tool_calls as a prefix + length."""
from __future__ import annotations

import inspect
import json
import sqlite3

import pytest

import dispatcher
import tool_hooks


@pytest.mark.parametrize("domain,action", sorted(tool_hooks._TRUNCATE_KEYS))
def test_truncate_keys_name_real_handler_parameters(domain, action):
    params = inspect.signature(dispatcher.resolve(domain, action)).parameters
    for key in tool_hooks._TRUNCATE_KEYS[(domain, action)]:
        assert key in params, f"{domain}__{action} has no parameter {key!r}"


def test_long_imessage_body_is_logged_truncated(tool_hints_db):
    with tool_hooks.tool_called("contacts", "search", {"name": "A"}) as h:
        h["result"] = [{"name": "A"}]
    body = "x" * 500
    with tool_hooks.tool_called("imessage", "send", {"recipient": "A", "message": body}) as h:
        h["result"] = "sent"
    conn = sqlite3.connect(tool_hints_db)
    (args_json,) = conn.execute(
        "SELECT args_json FROM mcp_tool_calls WHERE domain='imessage' AND action='send'"
    ).fetchone()
    message = json.loads(args_json)["message"]
    assert message == "x" * tool_hooks._TRUNCATE_LEN + "... [500 chars]"
