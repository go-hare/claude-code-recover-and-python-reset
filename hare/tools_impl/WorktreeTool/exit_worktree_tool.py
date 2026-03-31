"""
Exit Worktree Tool - return from a git worktree.

Port of: src/tools/ExitWorktreeTool/ExitWorktreeTool.ts
"""

from __future__ import annotations

import asyncio
from typing import Any

TOOL_NAME = "ExitWorktree"
DESCRIPTION = "Exit current worktree and return to the main working directory"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "cleanup": {"type": "boolean", "description": "Remove worktree after exit"},
        },
    }


async def call(cleanup: bool = False, **kwargs: Any) -> dict[str, Any]:
    if cleanup:
        worktree_path = kwargs.get("worktree_path", "")
        if worktree_path:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "git", "worktree", "remove", worktree_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
            except Exception:
                pass
    return {"status": "exited", "cleanup": cleanup}
