"""
Task Stop Tool - stop a running task.

Port of: src/tools/TaskStopTool/TaskStopTool.ts
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "TaskStop"
DESCRIPTION = "Stop a running background task"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The task ID to stop"},
        },
        "required": ["task_id"],
    }


async def call(task_id: str, **kwargs: Any) -> dict[str, Any]:
    return {"task_id": task_id, "status": "stopped"}
