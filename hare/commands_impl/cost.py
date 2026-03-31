"""
/cost command - show session cost and duration.

Port of: src/commands/cost/cost.ts + index.ts
"""

from __future__ import annotations

from typing import Any

from hare.cost_tracker import get_total_cost, get_total_api_duration
from hare.utils.format import format_cost, format_duration

COMMAND_NAME = "cost"
DESCRIPTION = "Show the total cost and duration of the current session"


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /cost command."""
    cost = get_total_cost()
    duration = get_total_api_duration()

    lines = [
        "Session Statistics:",
        f"  Total cost: {format_cost(cost)}",
        f"  API duration: {format_duration(duration * 1000)}",
    ]
    return {"type": "text", "value": "\n".join(lines)}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "supports_non_interactive": True,
        "call": call,
    }
