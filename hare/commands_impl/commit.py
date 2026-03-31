"""Port of: src/commands/commit.ts"""
from __future__ import annotations
import asyncio
from typing import Any

COMMAND_NAME = "commit"
DESCRIPTION = "Create a git commit with a generated message"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    message = args.strip()
    if not message:
        return {"type": "error", "display_text": "Usage: /commit <message>"}
    proc = await asyncio.create_subprocess_exec(
        "git", "commit", "-m", message,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    output = (stdout or b"").decode("utf-8", errors="replace") + (stderr or b"").decode("utf-8", errors="replace")
    return {"type": "commit", "display_text": output.strip()}
