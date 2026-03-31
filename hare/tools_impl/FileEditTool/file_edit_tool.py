"""
FileEditTool - edit files using search and replace.

Port of: src/tools/FileEditTool/FileEditTool.ts + types.ts + utils.ts

Performs exact string replacement in files.
"""

from __future__ import annotations

import os
from typing import Any, Optional

FILE_EDIT_TOOL_NAME = "FileEdit"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file to edit"},
            "old_string": {"type": "string", "description": "The exact string to find"},
            "new_string": {"type": "string", "description": "The replacement string"},
            "replace_all": {"type": "boolean", "description": "Replace all occurrences"},
        },
        "required": ["file_path", "old_string", "new_string"],
    }


async def call(
    tool_input: dict[str, Any],
    *,
    cwd: str = "",
) -> dict[str, Any]:
    """Edit a file using search and replace."""
    file_path = tool_input.get("file_path", "")
    old_string = tool_input.get("old_string", "")
    new_string = tool_input.get("new_string", "")
    replace_all = tool_input.get("replace_all", False)

    if not file_path:
        return {"type": "error", "error": "file_path is required"}
    if not old_string:
        return {"type": "error", "error": "old_string is required"}
    if old_string == new_string:
        return {"type": "error", "error": "old_string and new_string must be different"}

    full_path = os.path.join(cwd, file_path) if cwd and not os.path.isabs(file_path) else file_path

    if not os.path.exists(full_path):
        return {"type": "error", "error": f"File not found: {file_path}"}

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {"type": "error", "error": f"Failed to read file: {e}"}

    if old_string not in content:
        return {"type": "error", "error": "old_string not found in file"}

    if not replace_all:
        count = content.count(old_string)
        if count > 1:
            return {
                "type": "error",
                "error": f"old_string found {count} times. Use replace_all=true or provide more context.",
            }
        new_content = content.replace(old_string, new_string, 1)
    else:
        new_content = content.replace(old_string, new_string)

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        return {"type": "error", "error": f"Failed to write file: {e}"}

    # Calculate diff info
    old_lines = old_string.count("\n") + 1
    new_lines = new_string.count("\n") + 1
    replacements = content.count(old_string) if replace_all else 1

    return {
        "type": "tool_result",
        "content": f"Edited {file_path}: replaced {replacements} occurrence(s), {old_lines} line(s) → {new_lines} line(s)",
        "is_error": False,
    }


def compute_diff(old: str, new: str) -> str:
    """Compute a simple diff between two strings."""
    import difflib
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, lineterm="")
    return "".join(diff)
