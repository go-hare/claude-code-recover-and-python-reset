from __future__ import annotations

import asyncio
from typing import Any, Sequence

from claude_code_py.engine.models import (
    AssistantMessage,
    ConversationMessage,
    TextBlock,
    ToolResultMessage,
    ToolSchema,
    ToolUseBlock,
    UserMessage,
)


class AnthropicSDKClient:
    """Best-effort adapter around the Python Anthropics SDK."""

    def __init__(self, api_key: str | None = None) -> None:
        try:
            from anthropic import Anthropic
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Install the optional dependency with: pip install -e .[anthropic]"
            ) from exc

        self._client = Anthropic(api_key=api_key)

    async def create_assistant_message(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ConversationMessage],
        tools: Sequence[ToolSchema],
        model: str,
        max_output_tokens: int,
    ) -> AssistantMessage:
        return await asyncio.to_thread(
            self._create_assistant_message_sync,
            system_prompt=system_prompt,
            messages=messages,
            tools=tools,
            model=model,
            max_output_tokens=max_output_tokens,
        )

    def _create_assistant_message_sync(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ConversationMessage],
        tools: Sequence[ToolSchema],
        model: str,
        max_output_tokens: int,
    ) -> AssistantMessage:
        sdk_messages = [self._to_sdk_message(message) for message in messages]
        response = self._client.messages.create(
            model=model,
            system=system_prompt,
            messages=sdk_messages,
            tools=[self._to_sdk_tool_schema(tool) for tool in tools],
            max_tokens=max_output_tokens,
        )

        blocks: list[TextBlock | ToolUseBlock] = []
        for block in getattr(response, "content", []):
            block_type = getattr(block, "type", None)
            if block_type == "text":
                blocks.append(TextBlock(text=getattr(block, "text", "")))
                continue
            if block_type == "tool_use":
                blocks.append(
                    ToolUseBlock(
                        id=str(getattr(block, "id", "")),
                        name=str(getattr(block, "name", "")),
                        input=dict(getattr(block, "input", {}) or {}),
                    )
                )

        return AssistantMessage(
            blocks=blocks,
            request_id=str(getattr(response, "id", "")) or None,
        )

    @staticmethod
    def _to_sdk_tool_schema(tool: ToolSchema) -> dict[str, Any]:
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
        }

    @staticmethod
    def _to_sdk_message(message: ConversationMessage) -> dict[str, Any]:
        if isinstance(message, UserMessage):
            return {"role": "user", "content": message.content}

        if isinstance(message, ToolResultMessage):
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": message.tool_use_id,
                        "content": message.content,
                        "is_error": message.is_error,
                    }
                ],
            }

        content: list[dict[str, Any]] = []
        for block in message.blocks:
            if isinstance(block, TextBlock):
                content.append({"type": "text", "text": block.text})
            elif isinstance(block, ToolUseBlock):
                content.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
        return {"role": "assistant", "content": content}
