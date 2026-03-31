"""
/upgrade command.

Port of: src/commands/upgrade/index.ts
"""

from __future__ import annotations

from typing import Any

COMMAND_NAME = "upgrade"
DESCRIPTION = "Upgrade to Max for higher rate limits and more Opus"


async def call(args: str, **context: Any) -> dict[str, Any]:
    return {"type": "text", "value": "Visit https://claude.ai/settings to manage your subscription."}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "call": call,
    }
