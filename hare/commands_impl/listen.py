"""Port of: src/commands/listen.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "listen"
DESCRIPTION = "Toggle voice input mode"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    return {"type": "listen", "display_text": "Voice input not available in Python port."}
