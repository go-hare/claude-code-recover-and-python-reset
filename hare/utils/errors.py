"""
Error utilities.

Port of: src/utils/errors.ts
"""

from __future__ import annotations

from typing import Any


def error_message(error: Any) -> str:
    """Extract an error message from any error type."""
    if isinstance(error, Exception):
        return str(error)
    return str(error)


def is_enoent(error: Any) -> bool:
    """Check if an error is a FileNotFoundError."""
    return isinstance(error, FileNotFoundError)


def is_abort_error(error: Any) -> bool:
    """Check if an error is an abort/cancellation error."""
    if isinstance(error, (KeyboardInterrupt, asyncio.CancelledError)):
        return True
    msg = error_message(error).lower()
    return "aborted" in msg or "cancelled" in msg


# Import asyncio only when needed
import asyncio
