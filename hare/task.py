"""
Task type definitions and ID generation.

Port of: src/Task.ts
"""

from __future__ import annotations

import os
import secrets
import string
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional

from hare.types.ids import AgentId

TaskType = Literal[
    "local_bash",
    "local_agent",
    "remote_agent",
    "in_process_teammate",
    "local_workflow",
    "monitor_mcp",
    "dream",
]

TaskStatus = Literal[
    "pending",
    "running",
    "completed",
    "failed",
    "killed",
]


def is_terminal_task_status(status: TaskStatus) -> bool:
    """True when a task is in a terminal state and will not transition further."""
    return status in ("completed", "failed", "killed")


@dataclass
class TaskHandle:
    task_id: str
    cleanup: Optional[Callable[[], None]] = None


SetAppState = Callable[[Callable[[Any], Any]], None]


@dataclass
class TaskContext:
    abort_controller: Any = None  # asyncio.Event or similar
    get_app_state: Optional[Callable[[], Any]] = None
    set_app_state: Optional[SetAppState] = None


@dataclass
class TaskStateBase:
    id: str = ""
    type: TaskType = "local_bash"
    status: TaskStatus = "pending"
    description: str = ""
    tool_use_id: Optional[str] = None
    start_time: float = 0.0
    end_time: Optional[float] = None
    total_paused_ms: Optional[float] = None
    output_file: str = ""
    output_offset: int = 0
    notified: bool = False


@dataclass
class LocalShellSpawnInput:
    command: str = ""
    description: str = ""
    timeout: Optional[float] = None
    tool_use_id: Optional[str] = None
    agent_id: Optional[AgentId] = None
    kind: Optional[Literal["bash", "monitor"]] = None


@dataclass
class Task:
    name: str = ""
    type: TaskType = "local_bash"

    async def kill(self, task_id: str, set_app_state: SetAppState) -> None:
        pass


# Task ID prefixes (same as TS)
_TASK_ID_PREFIXES: dict[str, str] = {
    "local_bash": "b",
    "local_agent": "a",
    "remote_agent": "r",
    "in_process_teammate": "t",
    "local_workflow": "w",
    "monitor_mcp": "m",
    "dream": "d",
}

# Case-insensitive-safe alphabet (digits + lowercase) for task IDs.
# 36^8 ≈ 2.8 trillion combinations.
_TASK_ID_ALPHABET = string.digits + string.ascii_lowercase


def _get_task_id_prefix(task_type: TaskType) -> str:
    return _TASK_ID_PREFIXES.get(task_type, "x")


def generate_task_id(task_type: TaskType) -> str:
    prefix = _get_task_id_prefix(task_type)
    rand_bytes = secrets.token_bytes(8)
    suffix = "".join(
        _TASK_ID_ALPHABET[b % len(_TASK_ID_ALPHABET)] for b in rand_bytes
    )
    return prefix + suffix


def get_task_output_path(task_id: str) -> str:
    """Return the output file path for a given task ID."""
    home = os.path.expanduser("~")
    return os.path.join(home, ".claude", "tasks", f"{task_id}.output")


def create_task_state_base(
    task_id: str,
    task_type: TaskType,
    description: str,
    tool_use_id: Optional[str] = None,
) -> TaskStateBase:
    import time

    return TaskStateBase(
        id=task_id,
        type=task_type,
        status="pending",
        description=description,
        tool_use_id=tool_use_id,
        start_time=time.time() * 1000,  # ms since epoch, like Date.now()
        output_file=get_task_output_path(task_id),
        output_offset=0,
        notified=False,
    )
