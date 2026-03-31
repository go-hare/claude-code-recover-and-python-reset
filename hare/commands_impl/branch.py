"""Port of: src/commands/branch.ts"""
from __future__ import annotations
import asyncio
from typing import Any

COMMAND_NAME = "branch"
DESCRIPTION = "Show or create git branches"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    if args.strip():
        proc = await asyncio.create_subprocess_exec(
            "git", "checkout", "-b", args.strip(),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = (stdout or stderr).decode("utf-8", errors="replace")
        return {"type": "branch", "display_text": output.strip()}
    proc = await asyncio.create_subprocess_exec(
        "git", "branch", "--list",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace") if stdout else stderr.decode("utf-8", errors="replace")
    return {"type": "branch", "display_text": output.strip() or "No branches found"}
