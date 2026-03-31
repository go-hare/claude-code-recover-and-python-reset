"""Port of: src/commands/pr.ts"""
from __future__ import annotations
import asyncio
from typing import Any

COMMAND_NAME = "pr"
DESCRIPTION = "Create or view pull requests"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    subcmd = args.strip() or "list"
    cmd_parts = ["gh", "pr"] + subcmd.split()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = (stdout or stderr).decode("utf-8", errors="replace")
        return {"type": "pr", "display_text": output.strip()}
    except Exception as e:
        return {"type": "error", "display_text": f"PR command failed: {e}"}
