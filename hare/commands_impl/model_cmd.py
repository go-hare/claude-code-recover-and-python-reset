"""
/model command - set the AI model.

Port of: src/commands/model/index.ts
"""

from __future__ import annotations

from typing import Any

from hare.utils.model import normalize_model_string_for_api
from hare.utils.model.aliases import MODEL_ALIASES

COMMAND_NAME = "model"
DESCRIPTION = "Set the AI model for Claude Code"


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /model command."""
    if not args.strip():
        current = context.get("current_model", "unknown")
        lines = [f"Current model: {current}", "\nAvailable aliases:"]
        for alias, model_id in MODEL_ALIASES.items():
            lines.append(f"  {alias} -> {model_id}")
        return {"type": "text", "value": "\n".join(lines)}

    model_input = args.strip()
    resolved = normalize_model_string_for_api(model_input)
    return {"type": "model_change", "value": resolved, "display": model_input}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "argument_hint": "[model]",
        "call": call,
    }
