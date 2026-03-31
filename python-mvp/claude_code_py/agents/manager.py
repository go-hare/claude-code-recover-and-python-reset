from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable
from uuid import uuid4

from claude_code_py.engine.models import QueryResult


@dataclass(slots=True)
class AgentTaskHandle:
    task_id: str
    description: str


@dataclass(slots=True)
class AgentTaskSnapshot:
    task_id: str
    description: str
    status: str
    result: str | None
    error: str | None
    started_at: datetime
    completed_at: datetime | None


@dataclass(slots=True)
class _AgentTaskRecord:
    task_id: str
    description: str
    status: str
    started_at: datetime
    runner: Callable[[], Awaitable[QueryResult]]
    task: asyncio.Task[None] | None = None
    result: str | None = None
    error: str | None = None
    completed_at: datetime | None = None


class AgentTaskManager:
    """Track background subagents and their results."""

    def __init__(self) -> None:
        self._tasks: dict[str, _AgentTaskRecord] = {}

    def start(
        self,
        *,
        description: str,
        runner: Callable[[], Awaitable[QueryResult]],
    ) -> AgentTaskHandle:
        task_id = str(uuid4())
        record = _AgentTaskRecord(
            task_id=task_id,
            description=description,
            status="running",
            started_at=datetime.utcnow(),
            runner=runner,
        )
        record.task = asyncio.create_task(self._run(record))
        self._tasks[task_id] = record
        return AgentTaskHandle(task_id=task_id, description=description)

    async def _run(self, record: _AgentTaskRecord) -> None:
        try:
            result = await record.runner()
            record.result = result.output_text
            record.status = "completed"
        except Exception as exc:  # noqa: BLE001 - background boundary
            record.error = str(exc)
            record.status = "failed"
        finally:
            record.completed_at = datetime.utcnow()

    def list_snapshots(self) -> list[AgentTaskSnapshot]:
        snapshots = [
            AgentTaskSnapshot(
                task_id=record.task_id,
                description=record.description,
                status=record.status,
                result=record.result,
                error=record.error,
                started_at=record.started_at,
                completed_at=record.completed_at,
            )
            for record in self._tasks.values()
        ]
        return sorted(snapshots, key=lambda item: item.started_at)

    async def wait(self, task_id: str) -> AgentTaskSnapshot:
        record = self._tasks[task_id]
        if record.task is not None:
            await record.task
        return AgentTaskSnapshot(
            task_id=record.task_id,
            description=record.description,
            status=record.status,
            result=record.result,
            error=record.error,
            started_at=record.started_at,
            completed_at=record.completed_at,
        )
