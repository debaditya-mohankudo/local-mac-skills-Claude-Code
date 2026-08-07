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
