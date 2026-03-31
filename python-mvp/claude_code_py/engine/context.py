from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from claude_code_py.engine.models import QueryResult

if TYPE_CHECKING:
    from claude_code_py.agents.manager import AgentTaskHandle, AgentTaskManager
    from claude_code_py.permissions.policy import PermissionPolicy
    from claude_code_py.tools.registry import ToolRegistry


class AgentRunner(Protocol):
    """Behavior needed by the agent tool."""

    async def run_subagent(
        self,
        *,
        prompt: str,
        description: str,
        allowed_tools: list[str] | None = None,
    ) -> QueryResult:
        ...

    def spawn_subagent(
        self,
        *,
        prompt: str,
        description: str,
        allowed_tools: list[str] | None = None,
        ) -> "AgentTaskHandle":
        ...


@dataclass(slots=True)
class ReadFileState:
    content: str
    timestamp: float
    offset: int | None = None
    limit: int | None = None

    @property
    def is_partial_view(self) -> bool:
        return self.offset not in {None, 0, 1} or self.limit is not None


@dataclass(slots=True)
class ToolContext:
    """Execution context shared by all tools."""

    cwd: Path
    permission_policy: "PermissionPolicy"
    registry: "ToolRegistry"
    agent_runner: AgentRunner
    task_manager: "AgentTaskManager"
    read_file_state: dict[str, ReadFileState]
    max_output_chars: int = 4000

    def resolve_path(self, raw_path: str) -> Path:
        path = Path(raw_path)
        if path.is_absolute():
            return path.resolve()
        return (self.cwd / path).resolve()
