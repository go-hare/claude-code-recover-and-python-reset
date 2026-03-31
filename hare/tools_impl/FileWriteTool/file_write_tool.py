"""
FileWriteTool - write/create files.

Port of: src/tools/FileWriteTool/FileWriteTool.ts + prompt.ts
"""

from __future__ import annotations

import os
from typing import Any

FILE_WRITE_TOOL_NAME = "FileWrite"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file to write"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["file_path", "content"],
    }


async def call(
    tool_input: dict[str, Any],
    *,
    cwd: str = "",
) -> dict[str, Any]:
    """Write content to a file."""
    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "")

    if not file_path:
        return {"type": "error", "error": "file_path is required"}

    full_path = os.path.join(cwd, file_path) if cwd and not os.path.isabs(file_path) else file_path

    try:
        os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return {"type": "error", "error": f"Failed to write: {e}"}

    lines = content.count("\n") + 1
    return {
        "type": "tool_result",
        "content": f"Wrote {lines} lines to {file_path}",
        "is_error": False,
    }
