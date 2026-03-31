"""
Enter Plan Mode Tool.

Port of: src/tools/EnterPlanModeTool/EnterPlanModeTool.ts

Switches the session into plan mode where Claude discusses
approaches without making changes.
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "EnterPlanMode"
DESCRIPTION = "Switch to plan mode for discussing approaches before coding"
PROMPT = """Use this tool to switch to plan mode. In plan mode, you can discuss approaches and design decisions without making any file changes. Use this when the task requires careful planning before implementation."""


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "reason": {"type": "string", "description": "Reason for entering plan mode"},
        },
    }


async def call(reason: str = "", **kwargs: Any) -> dict[str, Any]:
    return {"mode": "plan", "reason": reason}
