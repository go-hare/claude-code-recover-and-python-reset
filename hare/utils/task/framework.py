"""
Task framework.

Port of: src/utils/task/framework.ts
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TaskInfo:
    id: str
    name: str = ""
    status: str = "pending"
    result: Any = None
    error: str = ""


class TaskFramework:
    """Manages background tasks."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskInfo] = {}

    def create_task(self, name: str = "") -> str:
        task_id = str(uuid.uuid4())[:8]
        self._tasks[task_id] = TaskInfo(id=task_id, name=name)
        return task_id

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        return self._tasks.get(task_id)

    def list_tasks(self) -> list[TaskInfo]:
        return list(self._tasks.values())

    def update_task(self, task_id: str, **kwargs: Any) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        for k, v in kwargs.items():
            if hasattr(task, k):
                setattr(task, k, v)
        return True

    def complete_task(self, task_id: str, result: Any = None) -> bool:
        return self.update_task(task_id, status="completed", result=result)

    def fail_task(self, task_id: str, error: str = "") -> bool:
        return self.update_task(task_id, status="failed", error=error)

    def cancel_task(self, task_id: str) -> bool:
        return self.update_task(task_id, status="cancelled")
