"""Aarozi Healthcare — Standalone Windows Production Server Launcher.

This script starts the FastAPI backend + static Nuxt frontend in a single process
and serves the complete diagnostic laboratory system on port 8000 across the local LAN.
"""

from __future__ import annotations

import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

# Add current directory and parent paths
current_dir = Path(__file__).resolve().parent
repo_root = current_dir.parent.parent

if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Set default environment variables for standalone offline production
os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("HOST", "0.0.0.0")
os.environ.setdefault("PORT", "8000")

# If no DATABASE_URL is configured, use local SQLite database
db_path = current_dir / "dev_aarozi.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path}")

import uvicorn
from app.main import app


def open_browser_delayed(url: str, delay_seconds: float = 1.5) -> None:
    """Open default browser to the LIS dashboard after server boots."""
    def _open():
        time.sleep(delay_seconds)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    t = threading.Thread(target=_open, daemon=True)
    t.start()


def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    print("=" * 70)
    print("  AAROZI HEALTHCARE — PRODUCTION CLINICAL SYSTEM")
    print("=" * 70)
    print(f"  * Status:              Running")
    print(f"  * Local Access:        http://localhost:{port}")
    print(f"  * LAN Workstations:    http://<THIS-PC-IP>:{port}")
    print(f"  * Database:            {os.environ.get('DATABASE_URL')}")
    print(f"  * Mode:                OFFLINE_LOCAL (Zero Internet Required)")
    print("=" * 70)
    print("  Press CTRL+C in this terminal to safely stop the server.")
    print("=" * 70)

    # Launch browser automatically for seamless UX
    if os.environ.get("NO_BROWSER", "0") != "1":
        open_browser_delayed(f"http://localhost:{port}")

    # Run uvicorn server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    main()

