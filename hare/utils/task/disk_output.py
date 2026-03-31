"""
Task disk output.

Port of: src/utils/task/diskOutput.ts
"""

from __future__ import annotations

import json
import os
from typing import Any


def get_task_output_path(task_id: str, session_dir: str = "") -> str:
    """Get the file path for a task's output."""
    base = session_dir or os.path.join(os.path.expanduser("~"), ".claude", "tasks")
    return os.path.join(base, f"{task_id}.json")


def save_task_output(task_id: str, output: dict[str, Any], session_dir: str = "") -> str:
    """Save task output to disk."""
    path = get_task_output_path(task_id, session_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    return path


def load_task_output(task_id: str, session_dir: str = "") -> dict[str, Any] | None:
    """Load task output from disk."""
    path = get_task_output_path(task_id, session_dir)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
