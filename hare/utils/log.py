"""
Logging utilities.

Port of: src/utils/log.ts
"""

from __future__ import annotations

import sys


def log_error(error: Exception) -> None:
    """Log an error to stderr."""
    print(f"Error: {error}", file=sys.stderr)


def log_warning(message: str) -> None:
    """Log a warning to stderr."""
    print(f"Warning: {message}", file=sys.stderr)


def log_error_msg(message: str) -> None:
    """Log an error message string to stderr."""
    print(f"Error: {message}", file=sys.stderr)
