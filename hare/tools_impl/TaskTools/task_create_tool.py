"""
Task Create Tool - create background tasks.

Port of: src/tools/TaskCreateTool/TaskCreateTool.ts
"""

from __future__ import annotations

from typing import Any

from hare.task import generate_task_id

TOOL_NAME = "TaskCreate"
DESCRIPTION = "Create a new background task"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "description": {"type": "string", "description": "Task description"},
            "prompt": {"type": "string", "description": "The task prompt to execute"},
            "model": {"type": "string", "description": "Model to use (optional)"},
        },
        "required": ["description", "prompt"],
    }


async def call(description: str, prompt: str, model: str = "", **kwargs: Any) -> dict[str, Any]:
    task_id = generate_task_id()
    return {
        "task_id": task_id,
        "status": "created",
        "description": description,
    }
