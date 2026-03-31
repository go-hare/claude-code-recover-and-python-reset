"""
Task List Tool - list all tasks.

Port of: src/tools/TaskListTool/TaskListTool.ts
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "TaskList"
DESCRIPTION = "List all background tasks and their status"


def input_schema() -> dict[str, Any]:
    return {"type": "object", "properties": {}}


async def call(**kwargs: Any) -> dict[str, Any]:
    return {"tasks": [], "count": 0}
