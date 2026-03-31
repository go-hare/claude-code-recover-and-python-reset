"""
/status command - show Claude Code status.

Port of: src/commands/status/index.ts
"""

from __future__ import annotations

import os
import sys
from typing import Any

from hare.constants.product import VERSION, PRODUCT_NAME

COMMAND_NAME = "status"
DESCRIPTION = "Show Claude Code status including version, model, account, API connectivity"


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /status command."""
    lines = [
        f"{PRODUCT_NAME} Status:",
        f"  Version: {VERSION}",
        f"  Python: {sys.version.split()[0]}",
        f"  Platform: {sys.platform}",
        f"  CWD: {os.getcwd()}",
    ]

    # API key status
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    lines.append(f"  API Key: {'configured' if api_key else 'not set'}")

    # Current model
    model = context.get("current_model", "default")
    lines.append(f"  Model: {model}")

    return {"type": "text", "value": "\n".join(lines)}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "immediate": True,
        "call": call,
    }
