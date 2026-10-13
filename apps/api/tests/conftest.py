"""Pytest configuration for apps/api tests.

Inserts the apps/api directory into sys.path so that
`from app.main import app` resolves when pytest is invoked
from the repository root or any subdirectory.
"""

from __future__ import annotations

import sys
from pathlib import Path

# apps/api  (two levels up from this conftest)
_api_root = str(Path(__file__).resolve().parents[1])
if _api_root not in sys.path:
    sys.path.insert(0, _api_root)

# repo root  (four levels up — needed for contracts package)
_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
