"""Port of: src/commands/worktree.ts"""
from __future__ import annotations
import asyncio
from typing import Any

COMMAND_NAME = "worktree"
DESCRIPTION = "Manage git worktrees"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    subcmd = args.strip() or "list"
    cmd_parts = ["git", "worktree"] + subcmd.split()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = (stdout or stderr).decode("utf-8", errors="replace")
        return {"type": "worktree", "display_text": output.strip()}
    except Exception as e:
        return {"type": "error", "display_text": f"Worktree command failed: {e}"}
