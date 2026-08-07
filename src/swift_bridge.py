"""Thin wrapper that calls the local-mac-tool Swift CLI binary."""
import json
import subprocess
from typing import Any

from config import config as cfg

BINARY = cfg.swift_binary


def call_swift(command: str, payload: dict | None = None) -> Any:
    """Call a local-mac-tool command. Returns the data field on success, raises on error."""
    stdin = json.dumps(payload or {}).encode()
    result = subprocess.run(
        [BINARY, command],
        input=stdin,
        capture_output=True,
        timeout=60,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        try:
            err = json.loads(stderr)
            raise RuntimeError(err.get("message", stderr))
        except (json.JSONDecodeError, KeyError):
            raise RuntimeError(stderr or f"local-mac-tool exited {result.returncode}")
    envelope = json.loads(result.stdout)
    if envelope.get("status") != "ok":
        raise RuntimeError(envelope.get("message", "unknown error"))
    return envelope["data"]
