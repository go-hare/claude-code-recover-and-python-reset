"""
File utilities.

Port of: src/utils/file.ts

Low-level file operations: read, write, stat, modification time.
"""

from __future__ import annotations

import os
import time
from typing import Optional

FILE_NOT_FOUND_CWD_NOTE = "Make sure to use an absolute path, or the file is relative to CWD:"


def get_file_modification_time(file_path: str) -> int:
    """Get the last modification time of a file in milliseconds."""
    try:
        stat = os.stat(file_path)
        return int(stat.st_mtime * 1000)
    except OSError:
        return 0


def write_text_content(
    file_path: str,
    content: str,
    encoding: str = "utf-8",
    line_ending: str = "LF",
) -> None:
    """Write text content to a file, matching writeTextContent() in file.ts."""
    newline = "\n" if line_ending == "LF" else "\r\n"
    with open(file_path, "w", encoding=encoding, newline=newline) as f:
        f.write(content)


def read_file_sync_with_metadata(file_path: str) -> dict:
    """
    Read a file synchronously with metadata.
    Mirrors readFileSyncWithMetadata() in fileRead.ts.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        stat = os.stat(file_path)

        return {
            "content": content,
            "encoding": "utf-8",
            "mtime_ms": stat.st_mtime * 1000,
        }
    except FileNotFoundError:
        raise
    except Exception as e:
        raise


async def suggest_path_under_cwd(path: str) -> Optional[str]:
    """Suggest a corrected path under the current working directory."""
    from hare.utils.cwd import get_cwd
    basename = os.path.basename(path)
    candidate = os.path.join(get_cwd(), basename)
    if os.path.exists(candidate):
        return candidate
    return None
