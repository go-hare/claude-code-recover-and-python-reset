"""
/hooks command - manage hooks.

Port of: src/commands/hooks/index.ts
"""

from __future__ import annotations

from typing import Any

from hare.utils.hooks.hook_events import HOOK_EVENTS
from hare.utils.hooks.hook_registry import get_hook_registry

COMMAND_NAME = "hooks"
DESCRIPTION = "View registered hooks"


async def call(args: str, **context: Any) -> dict[str, Any]:
    registry = get_hook_registry()
    lines = ["Registered hooks:"]
    for event in HOOK_EVENTS:
        handlers = registry._handlers.get(event, [])
        if handlers:
            lines.append(f"  {event}: {len(handlers)} handler(s)")
    if len(lines) == 1:
        lines.append("  No hooks registered.")
    return {"type": "text", "value": "\n".join(lines)}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "call": call,
    }
