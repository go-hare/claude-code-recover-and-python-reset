"""
Sleep prevention service.

Port of: src/services/preventSleep.ts

Uses macOS 'caffeinate' to prevent idle sleep during long operations.
No-op on non-macOS platforms.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Optional

CAFFEINATE_TIMEOUT_SECONDS = 300  # 5 minutes

_caffeinate_proc: Optional[subprocess.Popen] = None
_ref_count = 0


def start_prevent_sleep() -> None:
    """Increment ref count and start preventing sleep if needed."""
    global _ref_count
    _ref_count += 1
    if _ref_count == 1:
        _spawn_caffeinate()


def stop_prevent_sleep() -> None:
    """Decrement ref count and allow sleep if no more work pending."""
    global _ref_count
    if _ref_count > 0:
        _ref_count -= 1
    if _ref_count == 0:
        _kill_caffeinate()


def force_stop_prevent_sleep() -> None:
    """Force stop preventing sleep."""
    global _ref_count
    _ref_count = 0
    _kill_caffeinate()


def _spawn_caffeinate() -> None:
    """Spawn caffeinate process on macOS."""
    global _caffeinate_proc
    if sys.platform != "darwin":
        return
    if _caffeinate_proc is not None:
        return
    try:
        _caffeinate_proc = subprocess.Popen(
            ["caffeinate", "-i", "-t", str(CAFFEINATE_TIMEOUT_SECONDS)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, OSError):
        _caffeinate_proc = None


def _kill_caffeinate() -> None:
    """Kill caffeinate process."""
    global _caffeinate_proc
    if _caffeinate_proc is not None:
        try:
            _caffeinate_proc.kill()
        except (ProcessLookupError, OSError):
            pass
        _caffeinate_proc = None
