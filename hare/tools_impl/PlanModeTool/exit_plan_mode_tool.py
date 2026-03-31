"""
Exit Plan Mode Tool.

Port of: src/tools/ExitPlanModeTool/ExitPlanModeV2Tool.ts

Switches back from plan mode to normal execution mode.
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "ExitPlanMode"
DESCRIPTION = "Exit plan mode and return to normal execution"
PROMPT = """Use this tool to exit plan mode and return to normal operation where you can make file changes and execute commands."""


def input_schema() -> dict[str, Any]:
    return {"type": "object", "properties": {}}


async def call(**kwargs: Any) -> dict[str, Any]:
    return {"mode": "default"}
