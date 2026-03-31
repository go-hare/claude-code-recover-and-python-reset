"""Port of: src/commands/rename.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "rename"
DESCRIPTION = "Rename the current conversation"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    name = args.strip()
    if not name:
        return {"type": "error", "display_text": "Usage: /rename <name>"}
    return {"type": "rename", "name": name, "display_text": f"Conversation renamed to: {name}"}
