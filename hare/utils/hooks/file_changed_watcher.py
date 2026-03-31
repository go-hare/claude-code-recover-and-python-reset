"""
File change watcher.

Port of: src/utils/hooks/fileChangedWatcher.ts

Watches for file changes and tracks modification timestamps.
"""

from __future__ import annotations

import os
import time
from typing import Callable, Optional


class FileChangedWatcher:
    """Watches files for changes based on modification time."""

    def __init__(self) -> None:
        self._timestamps: dict[str, float] = {}
        self._callbacks: list[Callable[[str], None]] = []

    def track(self, file_path: str) -> None:
        """Start tracking a file."""
        try:
            mtime = os.path.getmtime(file_path)
        except OSError:
            mtime = 0.0
        self._timestamps[file_path] = mtime

    def check(self, file_path: str) -> bool:
        """Check if a file has changed since last tracked."""
        try:
            current_mtime = os.path.getmtime(file_path)
        except OSError:
            return False

        prev_mtime = self._timestamps.get(file_path, 0.0)
        if current_mtime > prev_mtime:
            self._timestamps[file_path] = current_mtime
            return True
        return False

    def check_all(self) -> list[str]:
        """Check all tracked files. Returns list of changed file paths."""
        changed: list[str] = []
        for path in list(self._timestamps.keys()):
            if self.check(path):
                changed.append(path)
        return changed

    def on_change(self, callback: Callable[[str], None]) -> None:
        """Register a callback for file changes."""
        self._callbacks.append(callback)

    def poll(self) -> list[str]:
        """Poll for changes and notify callbacks."""
        changed = self.check_all()
        for path in changed:
            for cb in self._callbacks:
                try:
                    cb(path)
                except Exception:
                    pass
        return changed

    def untrack(self, file_path: str) -> None:
        """Stop tracking a file."""
        self._timestamps.pop(file_path, None)

    def clear(self) -> None:
        """Clear all tracked files."""
        self._timestamps.clear()
        self._callbacks.clear()
