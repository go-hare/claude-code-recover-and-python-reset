"""
File history tracking.

Port of: src/utils/fileHistory.ts

Tracks file modifications during a session for undo/redo and diff display.
"""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FileVersion:
    """A snapshot of a file's contents at a point in time."""
    path: str
    content: str
    timestamp: float = 0.0
    hash: str = ""
    tool_use_id: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()
        if not self.hash:
            self.hash = hashlib.sha256(self.content.encode()).hexdigest()[:12]


@dataclass
class FileHistoryEntry:
    """History of changes to a single file."""
    path: str
    versions: list[FileVersion] = field(default_factory=list)
    original_content: Optional[str] = None

    @property
    def current_version(self) -> Optional[FileVersion]:
        return self.versions[-1] if self.versions else None

    @property
    def is_modified(self) -> bool:
        if not self.versions:
            return False
        if self.original_content is None:
            return True
        return self.versions[-1].content != self.original_content


class FileHistoryTracker:
    """Tracks file history across a session."""

    def __init__(self) -> None:
        self._entries: dict[str, FileHistoryEntry] = {}

    def record_before(self, path: str, content: str) -> None:
        """Record file content before a modification."""
        abs_path = os.path.abspath(path)
        if abs_path not in self._entries:
            self._entries[abs_path] = FileHistoryEntry(
                path=abs_path,
                original_content=content,
            )
            self._entries[abs_path].versions.append(
                FileVersion(path=abs_path, content=content, tool_use_id="original")
            )

    def record_after(self, path: str, content: str, tool_use_id: str = "") -> None:
        """Record file content after a modification."""
        abs_path = os.path.abspath(path)
        entry = self._entries.get(abs_path)
        if entry is None:
            entry = FileHistoryEntry(path=abs_path)
            self._entries[abs_path] = entry

        entry.versions.append(
            FileVersion(path=abs_path, content=content, tool_use_id=tool_use_id)
        )

    def get_history(self, path: str) -> Optional[FileHistoryEntry]:
        """Get the history for a file."""
        return self._entries.get(os.path.abspath(path))

    def get_modified_files(self) -> list[str]:
        """Get list of all modified file paths."""
        return [
            entry.path
            for entry in self._entries.values()
            if entry.is_modified
        ]

    def get_all_entries(self) -> dict[str, FileHistoryEntry]:
        """Get all history entries."""
        return dict(self._entries)

    def undo(self, path: str) -> Optional[str]:
        """Undo the last change to a file. Returns the previous content."""
        abs_path = os.path.abspath(path)
        entry = self._entries.get(abs_path)
        if entry is None or len(entry.versions) < 2:
            return None

        entry.versions.pop()
        return entry.versions[-1].content

    def clear(self) -> None:
        """Clear all history."""
        self._entries.clear()


_tracker: Optional[FileHistoryTracker] = None


def get_file_history_tracker() -> FileHistoryTracker:
    """Get the global file history tracker."""
    global _tracker
    if _tracker is None:
        _tracker = FileHistoryTracker()
    return _tracker
