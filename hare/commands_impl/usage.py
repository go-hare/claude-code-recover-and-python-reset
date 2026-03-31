"""
/usage command - show plan usage limits.

Port of: src/commands/usage/index.ts
"""

from __future__ import annotations

from typing import Any

from hare.cost_tracker import get_model_usage

COMMAND_NAME = "usage"
DESCRIPTION = "Show plan usage limits"


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /usage command."""
    usage = get_model_usage()
    lines = ["Usage by model:"]
    for model, data in usage.items():
        lines.append(f"  {model}:")
        lines.append(f"    Input tokens: {data.get('input_tokens', 0):,}")
        lines.append(f"    Output tokens: {data.get('output_tokens', 0):,}")
    if not usage:
        lines.append("  No API calls made yet.")
    return {"type": "text", "value": "\n".join(lines)}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "call": call,
    }
