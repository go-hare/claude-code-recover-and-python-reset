"""
/resume command - resume a previous conversation.

Port of: src/commands/resume/index.ts
"""

from __future__ import annotations

from typing import Any

COMMAND_NAME = "resume"
DESCRIPTION = "Resume a previous conversation"
ALIASES = ["continue"]


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /resume command."""
    query = args.strip()
    if not query:
        return {"type": "text", "value": "Usage: /resume [conversation id or search term]"}
    return {"type": "resume", "value": query}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "aliases": ALIASES,
        "argument_hint": "[conversation id or search term]",
        "call": call,
    }
