"""Pytest path setup.

pyproject sets `pythonpath = ["src"]` so `from config import ...` and
`from tools.* import ...` resolve. Server-side tests additionally need the
repo root on sys.path so `from server.core.* import ...` resolves.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


import pytest


@pytest.fixture
def tool_hints_db(tmp_path, monkeypatch):
    """Point tool_hooks' call log at a scratch DB, so tests never write the real one."""
    import tool_hooks
    path = tmp_path / "tool_hints.sqlite"
    monkeypatch.setattr(tool_hooks, "_DB_PATH", path)
    return path
