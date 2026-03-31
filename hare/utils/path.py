"""
Path utilities.

Port of: src/utils/path.ts

Handles path expansion, normalization, and relativization.
"""

from __future__ import annotations

import os
from pathlib import Path


def expand_path(path: str) -> str:
    """
    Expand a path (resolve ~, relative paths).
    Mirrors expandPath() in path.ts.
    """
    expanded = os.path.expanduser(path)
    if not os.path.isabs(expanded):
        from hare.utils.cwd import get_cwd
        expanded = os.path.join(get_cwd(), expanded)
    return os.path.normpath(expanded)


def to_relative_path(absolute_path: str) -> str:
    """
    Convert an absolute path to a relative one (relative to cwd).
    Mirrors toRelativePath() in path.ts.
    """
    from hare.utils.cwd import get_cwd
    cwd = get_cwd()
    try:
        rel = os.path.relpath(absolute_path, cwd)
        return rel.replace("\\", "/")
    except ValueError:
        return absolute_path.replace("\\", "/")


def is_under_directory(path: str, directory: str) -> bool:
    """Check if a path is under a given directory."""
    try:
        path_resolved = os.path.realpath(path)
        dir_resolved = os.path.realpath(directory)
        return path_resolved.startswith(dir_resolved + os.sep) or path_resolved == dir_resolved
    except (OSError, ValueError):
        return False
