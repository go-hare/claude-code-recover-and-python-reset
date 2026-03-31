"""
Session Memory - persistent memory across conversations.

Port of: src/services/SessionMemory/SessionMemory.ts

Manages a CLAUDE.md memory file that persists important context
across conversation sessions.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional


MEMORY_FILE_NAME = "CLAUDE.md"
MAX_MEMORY_SIZE = 50_000  # chars


@dataclass
class MemoryEntry:
    content: str
    timestamp: float = field(default_factory=time.time)
    source: str = ""


@dataclass
class SessionMemory:
    """Manages session memory (CLAUDE.md) files."""
    project_dir: str
    entries: list[MemoryEntry] = field(default_factory=list)
    _loaded: bool = False

    @property
    def memory_file_path(self) -> str:
        return os.path.join(self.project_dir, MEMORY_FILE_NAME)

    @property
    def user_memory_file_path(self) -> str:
        return os.path.join(os.path.expanduser("~"), ".claude", MEMORY_FILE_NAME)

    def load(self) -> str:
        """Load memory content from files."""
        content_parts: list[str] = []

        # User-level memory
        user_content = self._read_memory_file(self.user_memory_file_path)
        if user_content:
            content_parts.append(user_content)

        # Project-level memory
        project_content = self._read_memory_file(self.memory_file_path)
        if project_content:
            content_parts.append(project_content)

        self._loaded = True
        return "\n\n".join(content_parts)

    def append(self, content: str, source: str = "assistant") -> None:
        """Append content to the project memory file."""
        self.entries.append(MemoryEntry(content=content, source=source))
        self._write_memory_file(self.memory_file_path, content, append=True)

    def get_all_content(self) -> str:
        """Get combined memory content from all sources."""
        if not self._loaded:
            return self.load()
        return self.load()

    def _read_memory_file(self, path: str) -> str:
        """Read a memory file, returning empty string if not found."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content) > MAX_MEMORY_SIZE:
                content = content[:MAX_MEMORY_SIZE]
            return content
        except (FileNotFoundError, PermissionError):
            return ""

    def _write_memory_file(self, path: str, content: str, append: bool = False) -> None:
        """Write content to a memory file."""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            mode = "a" if append else "w"
            with open(path, mode, encoding="utf-8") as f:
                if append:
                    f.write(f"\n\n{content}")
                else:
                    f.write(content)
        except (PermissionError, OSError):
            pass


def setup_session_memory(project_dir: str) -> SessionMemory:
    """Create and initialize a SessionMemory instance."""
    memory = SessionMemory(project_dir=project_dir)
    memory.load()
    return memory


def get_memory_content(project_dir: str) -> str:
    """Quick helper to load and return all memory content."""
    memory = SessionMemory(project_dir=project_dir)
    return memory.load()
