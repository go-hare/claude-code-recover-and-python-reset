"""
Which utility - find executables on PATH.

Port of: src/utils/which.ts
"""

from __future__ import annotations

import shutil
from typing import Optional


async def which(executable: str) -> Optional[str]:
    """
    Find executable on PATH.
    Returns the full path or None if not found.
    """
    return shutil.which(executable)


def which_sync(executable: str) -> Optional[str]:
    """Synchronous version of which."""
    return shutil.which(executable)
