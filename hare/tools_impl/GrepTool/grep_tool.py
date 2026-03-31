"""
GrepTool - search file contents using ripgrep.

Port of: src/tools/GrepTool/GrepTool.ts + prompt.ts
"""

from __future__ import annotations

import asyncio
import shutil
from typing import Any

GREP_TOOL_NAME = "Grep"
MAX_RESULTS = 500


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search for"},
            "path": {"type": "string", "description": "Directory to search in"},
            "include": {"type": "string", "description": "File glob pattern to include"},
        },
        "required": ["pattern"],
    }


async def call(
    tool_input: dict[str, Any],
    *,
    cwd: str = "",
) -> dict[str, Any]:
    """Search file contents using ripgrep."""
    pattern = tool_input.get("pattern", "")
    search_path = tool_input.get("path", "")
    include = tool_input.get("include", "")

    if not pattern:
        return {"type": "error", "error": "pattern is required"}

    rg = shutil.which("rg")
    if not rg:
        return {"type": "error", "error": "ripgrep (rg) not found in PATH"}

    cmd = [rg, "--no-heading", "--line-number", "--color=never", f"--max-count={MAX_RESULTS}"]
    if include:
        cmd.extend(["--glob", include])
    cmd.append(pattern)
    cmd.append(search_path or ".")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd or None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode("utf-8", errors="replace")
        if not output.strip():
            return {"type": "tool_result", "content": "No matches found.", "is_error": False}
        lines = output.strip().split("\n")
        if len(lines) > MAX_RESULTS:
            lines = lines[:MAX_RESULTS]
            output = "\n".join(lines) + f"\n\n(showing first {MAX_RESULTS} results)"
        else:
            output = "\n".join(lines)
        return {"type": "tool_result", "content": output, "is_error": False}
    except asyncio.TimeoutError:
        return {"type": "error", "error": "Search timed out"}
    except Exception as e:
        return {"type": "error", "error": str(e)}
