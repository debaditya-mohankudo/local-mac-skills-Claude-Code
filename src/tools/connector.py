"""
connector.py
------------
MCP tool handlers for the local OpenConnector gateway (Gmail/Calendar/Drive
and other provider Actions), via connector.client.OpenConnectorClient.

Generic passthrough by design: OpenConnector's exact Gmail/Calendar/Drive
action ids haven't been catalogued yet (tracked separately) — list_actions
lets a caller discover them, execute_action runs any of them once known.
Provider-specific wrapper tools (e.g. connector__gmail_search) can be added
once that catalog is confirmed, without changing this module's shape.

Tools registered as domain 'connector':
  connector__health         — health-check the running container
  connector__list_actions   — discover available action ids, optionally by service
  connector__execute_action — run one action by id with a JSON input payload
"""
from __future__ import annotations

from connector.client import OpenConnectorClient, OpenConnectorError

_client = OpenConnectorClient()


def handle_health() -> dict:
    """Health-check the local OpenConnector container (GET /v1/health)."""
    try:
        return _client.health()
    except OpenConnectorError as e:
        return {"success": False, "error": str(e)}


def handle_list_actions(service: str = "") -> dict:
    """List available OpenConnector Actions, optionally filtered by provider service (e.g. 'gmail')."""
    try:
        return _client.list_actions(service=service)
    except OpenConnectorError as e:
        return {"success": False, "error": str(e)}


def handle_execute_action(
    action_id: str,
    input: dict | None = None,
    idempotency_key: str = "",
    alias: str = "",
) -> dict:
    """Execute one OpenConnector Action by id (e.g. 'gmail.search_threads') with a JSON input payload.

    Pass idempotency_key for mutating actions (create/delete) to make retries safe.
    Pass alias to select a named connection instead of the default one.
    """
    try:
        return _client.execute_action(
            action_id,
            input=input,
            idempotency_key=idempotency_key or None,
            alias=alias or None,
        )
    except OpenConnectorError as e:
        return {"success": False, "error": str(e)}
