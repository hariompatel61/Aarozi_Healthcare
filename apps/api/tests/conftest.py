"""Pytest configuration for apps/api tests.

Inserts the apps/api directory into sys.path so that
`from app.main import app` resolves when pytest is invoked
from the repository root or any subdirectory.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Dynamically ensure apps/api and repository root (with contracts) are in sys.path
_this = Path(__file__).resolve()
for parent in _this.parents:
    if (parent / "app").is_dir() and str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
    if (parent / "contracts").is_dir() and str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
