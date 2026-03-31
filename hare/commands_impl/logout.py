"""Port of: src/commands/logout.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "logout"
DESCRIPTION = "Log out of your Anthropic account"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    return {"type": "logout", "display_text": "Logout flow not yet implemented in Python port."}
