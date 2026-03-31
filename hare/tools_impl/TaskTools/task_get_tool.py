"""
Task Get Tool - get details of a specific task.

Port of: src/tools/TaskGetTool/TaskGetTool.ts
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "TaskGet"
DESCRIPTION = "Get details of a specific background task"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The task ID to look up"},
        },
        "required": ["task_id"],
    }


async def call(task_id: str, **kwargs: Any) -> dict[str, Any]:
    return {"task_id": task_id, "status": "not_found"}
