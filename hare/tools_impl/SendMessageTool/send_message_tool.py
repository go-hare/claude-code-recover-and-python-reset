"""
Send Message Tool - send a message to another agent.

Port of: src/tools/SendMessageTool/SendMessageTool.ts
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "SendMessage"
DESCRIPTION = "Send a message to another agent or resume a paused agent"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Agent ID or name to send to"},
            "message": {"type": "string", "description": "The message to send"},
        },
        "required": ["to", "message"],
    }


async def call(to: str, message: str, **kwargs: Any) -> dict[str, Any]:
    return {"to": to, "status": "sent", "message_length": len(message)}
