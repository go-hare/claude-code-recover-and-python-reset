"""
/version command.

Port of: src/commands/version.ts
"""

from __future__ import annotations

from typing import Any

from hare.constants.product import VERSION

COMMAND_NAME = "version"
DESCRIPTION = "Print the version"


async def call(args: str, **context: Any) -> dict[str, Any]:
    return {"type": "text", "value": VERSION}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "supports_non_interactive": True,
        "call": call,
    }
