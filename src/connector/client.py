"""
client.py
---------
Thin HTTP client for a locally-running OpenConnector gateway
(github.com/oomol-lab/open-connector), which fronts Gmail/Calendar/Drive
(and other) provider Actions behind one runtime.

Endpoints used (see docs/runtime-api.md in the OpenConnector repo):
  GET  /v1/health
  GET  /v1/actions[?service=<service>]
  GET  /v1/actions/:actionId
  POST /v1/actions/:actionId
"""
from __future__ import annotations

import requests

from config import config


class OpenConnectorError(RuntimeError):
    pass


class OpenConnectorClient:
    def __init__(self, base_url: str | None = None, runtime_token: str | None = None) -> None:
        self.base_url = (base_url or config.openconnector_base_url).rstrip("/")
        self.runtime_token = runtime_token or config.openconnector_runtime_token

    def _headers(self, idempotency_key: str | None = None, alias: str | None = None) -> dict:
        headers = {"content-type": "application/json"}
        if self.runtime_token:
            headers["authorization"] = f"Bearer {self.runtime_token}"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        if alias:
            headers["x-oo-connector-alias"] = alias
        return headers

    def _unwrap(self, resp: requests.Response) -> dict:
        try:
            body = resp.json()
        except ValueError:
            resp.raise_for_status()
            raise OpenConnectorError(f"non-JSON response: {resp.text[:200]}")
        if not resp.ok or not body.get("success", False):
            raise OpenConnectorError(body.get("message") or f"HTTP {resp.status_code}")
        return body

    def health(self) -> dict:
        resp = requests.get(f"{self.base_url}/v1/health", headers=self._headers(), timeout=10)
        return self._unwrap(resp)

    def list_actions(self, service: str = "") -> dict:
        params = {"service": service} if service else {}
        resp = requests.get(f"{self.base_url}/v1/actions", params=params, headers=self._headers(), timeout=10)
        return self._unwrap(resp)

    def get_action(self, action_id: str) -> dict:
        resp = requests.get(f"{self.base_url}/v1/actions/{action_id}", headers=self._headers(), timeout=10)
        return self._unwrap(resp)

    def execute_action(
        self,
        action_id: str,
        input: dict | None = None,
        idempotency_key: str | None = None,
        alias: str | None = None,
    ) -> dict:
        resp = requests.post(
            f"{self.base_url}/v1/actions/{action_id}",
            json={"input": input or {}},
            headers=self._headers(idempotency_key=idempotency_key, alias=alias),
            timeout=30,
        )
        return self._unwrap(resp)
