"""
Filesystem operations abstraction.

Port of: src/utils/fsOperations.ts

Provides an abstraction layer over filesystem operations to support
mocking in tests and symlink resolution for permission checks.
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Protocol


class FsOperations(Protocol):
    """Filesystem operations interface."""

    def exists_sync(self, path: str) -> bool: ...
    def read_file_sync(self, path: str, encoding: str = "utf-8") -> str: ...
    def write_file_sync(self, path: str, data: str, encoding: str = "utf-8") -> None: ...
    def mkdir(self, path: str, *, recursive: bool = True, mode: int = 0o755) -> None: ...
    def realpath_sync(self, path: str) -> str: ...
    def stat_sync(self, path: str) -> os.stat_result: ...
    def lstat_sync(self, path: str) -> os.stat_result: ...


class NodeFsOperations:
    """Default filesystem operations using os/pathlib."""

    def exists_sync(self, path: str) -> bool:
        return os.path.exists(path)

    def read_file_sync(self, path: str, encoding: str = "utf-8") -> str:
        with open(path, "r", encoding=encoding, errors="replace") as f:
            return f.read()

    def write_file_sync(self, path: str, data: str, encoding: str = "utf-8") -> None:
        with open(path, "w", encoding=encoding) as f:
            f.write(data)

    def mkdir(self, path: str, *, recursive: bool = True, mode: int = 0o755) -> None:
        os.makedirs(path, mode=mode, exist_ok=recursive)

    def realpath_sync(self, path: str) -> str:
        return os.path.realpath(path)

    def stat_sync(self, path: str) -> os.stat_result:
        return os.stat(path)

    def lstat_sync(self, path: str) -> os.stat_result:
        return os.lstat(path)


_fs_impl: Optional[NodeFsOperations] = None


def get_fs_implementation() -> NodeFsOperations:
    """Get the current filesystem implementation."""
    global _fs_impl
    if _fs_impl is None:
        _fs_impl = NodeFsOperations()
    return _fs_impl


def set_fs_implementation(impl: Any) -> None:
    """Set a custom filesystem implementation (for testing)."""
    global _fs_impl
    _fs_impl = impl


def safe_resolve_path(fs: Any, path: str) -> tuple[str, bool]:
    """
    Safely resolve a file path, following symlinks.
    Returns (resolved_path, is_symlink).
    """
    try:
        real = os.path.realpath(path)
        is_symlink = real != os.path.normpath(os.path.abspath(path))
        return real, is_symlink
    except OSError:
        return path, False


def get_paths_for_permission_check(path: str) -> list[str]:
    """
    Get all paths to check for permissions (original + resolved symlinks).
    This prevents bypassing permission checks via symlinks.
    """
    expanded = os.path.expanduser(path)
    abs_path = os.path.abspath(expanded)
    paths = [abs_path]

    try:
        real = os.path.realpath(abs_path)
        if real != abs_path:
            paths.append(real)
    except OSError:
        pass

    return paths


def is_duplicate_path(path_a: str, path_b: str) -> bool:
    """Check if two paths resolve to the same file."""
    try:
        return os.path.realpath(path_a) == os.path.realpath(path_b)
    except OSError:
        return path_a == path_b


@dataclass
class ReadFileRangeResult:
    """Result of reading a range of lines from a file."""
    content: str
    total_lines: int
    start_line: int
    end_line: int


def read_file_range(
    path: str,
    start_line: int = 0,
    end_line: Optional[int] = None,
) -> ReadFileRangeResult:
    """Read a range of lines from a file."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    total = len(all_lines)
    start = max(0, start_line)
    end = min(total, end_line) if end_line is not None else total

    selected = all_lines[start:end]

    return ReadFileRangeResult(
        content="".join(selected),
        total_lines=total,
        start_line=start,
        end_line=end,
    )


def tail_file(path: str, num_lines: int = 100) -> str:
    """Read the last N lines of a file."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()
    return "".join(all_lines[-num_lines:])
