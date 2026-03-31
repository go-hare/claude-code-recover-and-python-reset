"""Port of: src/commands/login.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "login"
DESCRIPTION = "Log in to your Anthropic account"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    return {"type": "login", "display_text": "Login flow not yet implemented in Python port."}
