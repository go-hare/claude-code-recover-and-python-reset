"""
/session command - show session info.

Port of: src/commands/session/index.ts
"""

from __future__ import annotations

from typing import Any

COMMAND_NAME = "session"
DESCRIPTION = "Show session info"


async def call(args: str, **context: Any) -> dict[str, Any]:
    session_id = context.get("session_id", "unknown")
    return {"type": "text", "value": f"Session ID: {session_id}"}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "call": call,
    }
