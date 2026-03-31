"""Port of: src/commands/stash.ts"""
from __future__ import annotations
import asyncio
from typing import Any

COMMAND_NAME = "stash"
DESCRIPTION = "Stash or unstash git changes"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    subcmd = args.strip() or "list"
    cmd_parts = ["git", "stash"] + subcmd.split()
    proc = await asyncio.create_subprocess_exec(
        *cmd_parts,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    output = (stdout or stderr).decode("utf-8", errors="replace")
    return {"type": "stash", "display_text": output.strip() or "No stash entries."}
