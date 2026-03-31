"""
FileReadTool - read file contents.

Port of: src/tools/FileReadTool/FileReadTool.ts + prompt.ts + limits.ts

Reads files with line numbering, offset/limit, and image support.
"""

from __future__ import annotations

import base64
import mimetypes
import os
from typing import Any, Optional

FILE_READ_TOOL_NAME = "FileRead"
MAX_LINES_TO_READ = 2000
MAX_FILE_SIZE = 500_000
FILE_UNCHANGED_STUB = "[File unchanged since last read]"

IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"})


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file to read"},
            "offset": {"type": "integer", "description": "Line number to start from (1-indexed)"},
            "limit": {"type": "integer", "description": "Max number of lines to read"},
        },
        "required": ["file_path"],
    }


async def call(
    tool_input: dict[str, Any],
    *,
    cwd: str = "",
) -> dict[str, Any]:
    """Read a file and return its contents."""
    file_path = tool_input.get("file_path", "")
    offset = tool_input.get("offset", 0)
    limit = tool_input.get("limit", 0)

    if not file_path:
        return {"type": "error", "error": "file_path is required"}

    full_path = os.path.join(cwd, file_path) if cwd and not os.path.isabs(file_path) else file_path

    if not os.path.exists(full_path):
        return {"type": "error", "error": f"File not found: {file_path}"}

    # Check if image
    ext = os.path.splitext(full_path)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        return await _read_image(full_path)

    # Check file size
    try:
        size = os.path.getsize(full_path)
        if size > MAX_FILE_SIZE:
            return {
                "type": "error",
                "error": f"File too large ({size:,} bytes). Max: {MAX_FILE_SIZE:,}",
            }
    except OSError as e:
        return {"type": "error", "error": str(e)}

    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
    except Exception as e:
        return {"type": "error", "error": f"Failed to read: {e}"}

    total = len(all_lines)

    # Apply offset/limit
    if offset > 0:
        start = offset - 1
    elif offset < 0:
        start = max(0, total + offset)
    else:
        start = 0

    if limit > 0:
        end = min(start + limit, total)
    else:
        end = min(start + MAX_LINES_TO_READ, total)

    selected = all_lines[start:end]

    # Format with line numbers
    numbered = []
    for i, line in enumerate(selected, start=start + 1):
        numbered.append(f"{i:6d}|{line.rstrip()}")

    content = "\n".join(numbered)
    if not content:
        content = "File is empty."

    return {
        "type": "tool_result",
        "content": content,
        "is_error": False,
        "metadata": {
            "file_path": file_path,
            "total_lines": total,
            "lines_shown": len(selected),
        },
    }


async def _read_image(path: str) -> dict[str, Any]:
    """Read an image file and return base64 content."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        mime = mimetypes.guess_type(path)[0] or "image/png"
        b64 = base64.b64encode(data).decode("ascii")
        return {
            "type": "tool_result",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime,
                        "data": b64[:100] + "...[truncated for display]",
                    },
                }
            ],
            "is_error": False,
        }
    except Exception as e:
        return {"type": "error", "error": f"Failed to read image: {e}"}
