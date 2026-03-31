"""
Glob utilities.

Port of: src/utils/glob.ts

Wraps Python's glob module with permission filtering.
"""

from __future__ import annotations

import glob as _glob_module
import os
from typing import Any, Optional

from hare.types.permissions import ToolPermissionContext


async def glob(
    pattern: str,
    base_path: str,
    options: dict[str, Any] | None = None,
    signal: Any = None,
    permission_context: Optional[ToolPermissionContext] = None,
) -> dict[str, Any]:
    """
    Search for files matching a glob pattern.
    Returns {"files": [...], "truncated": bool}.
    """
    opts = options or {}
    limit = opts.get("limit", 100)
    offset = opts.get("offset", 0)

    # Build full pattern
    if not pattern.startswith("**/") and not os.path.isabs(pattern):
        full_pattern = os.path.join(base_path, "**", pattern)
    else:
        full_pattern = os.path.join(base_path, pattern)

    matches = _glob_module.glob(full_pattern, recursive=True)

    # Filter to files only
    files = [f for f in matches if os.path.isfile(f)]

    # Sort by mtime (newest first)
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)

    # Apply offset
    files = files[offset:]

    # Check truncation
    truncated = len(files) > limit
    files = files[:limit]

    return {"files": files, "truncated": truncated}
