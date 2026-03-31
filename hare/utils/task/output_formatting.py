"""
Task output formatting.

Port of: src/utils/task/outputFormatting.ts
"""

from __future__ import annotations

from typing import Any


def format_task_output(task: dict[str, Any]) -> str:
    """Format a task result for display."""
    status = task.get("status", "unknown")
    task_id = task.get("id", "")
    name = task.get("name", "")

    header = f"Task {task_id}"
    if name:
        header += f" ({name})"
    header += f" - {status}"

    result = task.get("result", "")
    if isinstance(result, dict):
        lines = [f"  {k}: {v}" for k, v in result.items()]
        result = "\n".join(lines)

    return f"{header}\n{result}" if result else header
