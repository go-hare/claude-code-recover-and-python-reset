"""
/clear command - clear conversation history.

Port of: src/commands/clear/clear.ts + index.ts
"""

from __future__ import annotations

from typing import Any

COMMAND_NAME = "clear"
DESCRIPTION = "Clear conversation history and free up context"
ALIASES = ["reset", "new"]


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /clear command."""
    return {"type": "clear", "value": ""}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "aliases": ALIASES,
        "call": call,
    }
