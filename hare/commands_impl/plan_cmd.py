"""
/plan command - enter plan mode.

Port of: src/commands/plan/index.ts
"""

from __future__ import annotations

from typing import Any

COMMAND_NAME = "plan"
DESCRIPTION = "Enter plan mode to discuss approaches before coding"


async def call(args: str, **context: Any) -> dict[str, Any]:
    return {"type": "mode_change", "value": "plan"}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "call": call,
    }
