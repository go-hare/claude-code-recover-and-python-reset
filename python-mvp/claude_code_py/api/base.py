from __future__ import annotations

from typing import Protocol, Sequence

from claude_code_py.engine.models import (
    AssistantMessage,
    ConversationMessage,
    ToolSchema,
)


class ModelClient(Protocol):
    """Abstract model interface used by the query loop."""

    async def create_assistant_message(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ConversationMessage],
        tools: Sequence[ToolSchema],
        model: str,
        max_output_tokens: int,
    ) -> AssistantMessage:
        ...
