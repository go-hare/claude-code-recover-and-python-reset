"""
GlobTool - find files by glob pattern.

Port of: src/tools/GlobTool/GlobTool.ts + prompt.ts
"""

from __future__ import annotations

import glob
import os
from typing import Any

GLOB_TOOL_NAME = "Glob"
MAX_RESULTS = 500


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern to match"},
            "path": {"type": "string", "description": "Directory to search in"},
        },
        "required": ["pattern"],
    }


async def call(
    tool_input: dict[str, Any],
    *,
    cwd: str = "",
) -> dict[str, Any]:
    """Find files matching a glob pattern."""
    pattern = tool_input.get("pattern", "")
    search_path = tool_input.get("path", "")

    if not pattern:
        return {"type": "error", "error": "pattern is required"}

    base = search_path or cwd or "."
    if not pattern.startswith("**/") and not os.path.isabs(pattern):
        pattern = os.path.join("**", pattern)

    full_pattern = os.path.join(base, pattern)

    try:
        matches = sorted(glob.glob(full_pattern, recursive=True))[:MAX_RESULTS]
    except Exception as e:
        return {"type": "error", "error": str(e)}

    if not matches:
        return {"type": "tool_result", "content": "No files matched.", "is_error": False}

    # Make paths relative to base
    rel_matches = []
    for m in matches:
        try:
            rel_matches.append(os.path.relpath(m, base))
        except ValueError:
            rel_matches.append(m)

    content = "\n".join(rel_matches)
    if len(matches) >= MAX_RESULTS:
        content += f"\n\n(showing first {MAX_RESULTS} of many matches)"

    return {"type": "tool_result", "content": content, "is_error": False}
