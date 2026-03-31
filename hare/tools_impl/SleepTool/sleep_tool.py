"""
Sleep Tool - wait for a specified duration.

Port of: src/tools/SleepTool/prompt.ts
"""

from __future__ import annotations

import asyncio
from typing import Any

TOOL_NAME = "Sleep"
DESCRIPTION = "Wait for a specified number of seconds"
PROMPT = """Waits for a specified duration. Use when you need to pause before checking on something."""


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "seconds": {
                "type": "number",
                "description": "Seconds to sleep (max 300)",
            },
        },
        "required": ["seconds"],
    }


async def call(seconds: float, **kwargs: Any) -> dict[str, Any]:
    clamped = min(max(seconds, 0), 300)
    await asyncio.sleep(clamped)
    return {"slept_seconds": clamped}
