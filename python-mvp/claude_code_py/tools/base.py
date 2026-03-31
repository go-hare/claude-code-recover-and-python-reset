from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from claude_code_py.engine.context import ToolContext
from claude_code_py.engine.models import ToolRunResult, ToolSchema


class Tool(ABC):
    """Base class for tools exposed to the model."""

    name: str
    aliases: tuple[str, ...] = ()
    description: str
    input_schema: dict[str, Any]

    @abstractmethod
    async def run(
        self,
        tool_input: Mapping[str, Any],
        context: ToolContext,
    ) -> ToolRunResult:
        """Execute the tool and return a model-visible result."""

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
        )
