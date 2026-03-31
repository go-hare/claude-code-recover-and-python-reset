"""
Enter Worktree Tool - switch to a git worktree.

Port of: src/tools/EnterWorktreeTool/EnterWorktreeTool.ts
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

TOOL_NAME = "EnterWorktree"
DESCRIPTION = "Switch to a git worktree for isolated changes"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "branch": {"type": "string", "description": "Branch name for the worktree"},
            "path": {"type": "string", "description": "Path for the worktree (optional)"},
        },
        "required": ["branch"],
    }


async def call(branch: str, path: str = "", **kwargs: Any) -> dict[str, Any]:
    if not path:
        path = os.path.join(os.getcwd(), f".worktree-{branch}")
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "worktree", "add", path, "-b", branch,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            return {"worktree_path": path, "branch": branch, "status": "created"}
        return {"error": stderr.decode("utf-8", errors="replace")}
    except Exception as e:
        return {"error": str(e)}
