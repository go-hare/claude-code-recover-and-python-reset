"""
Debug utilities.

Port of: src/utils/debug.ts
"""

from __future__ import annotations

import os
import sys


def log_for_debugging(message: str) -> None:
    """Log a debug message if verbose mode is enabled."""
    if os.environ.get("CLAUDE_CODE_DEBUG") == "1":
        print(f"[DEBUG] {message}", file=sys.stderr)


def log_error(error: Exception) -> None:
    """Log an error for debugging."""
    if os.environ.get("CLAUDE_CODE_DEBUG") == "1":
        print(f"[ERROR] {error}", file=sys.stderr)
