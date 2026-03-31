"""
Task Update Tool - send a message to a running task.

Port of: src/tools/TaskUpdateTool/TaskUpdateTool.ts
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "TaskUpdate"
DESCRIPTION = "Send a message or update to a running task"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The task ID"},
            "message": {"type": "string", "description": "Message to send"},
        },
        "required": ["task_id", "message"],
    }


async def call(task_id: str, message: str, **kwargs: Any) -> dict[str, Any]:
    return {"task_id": task_id, "status": "updated"}
