from __future__ import annotations

from typing import Iterable

from claude_code_py.api.base import ModelClient
from claude_code_py.engine.context import ToolContext
from claude_code_py.engine.models import (
    ConversationMessage,
    QueryResult,
    ToolResultMessage,
    ToolUseBlock,
)
from claude_code_py.tools.registry import ToolRegistry


async def execute_tool_use(
    tool_use: ToolUseBlock,
    *,
    registry: ToolRegistry,
    context: ToolContext,
    background: bool,
) -> ToolResultMessage:
    """Run one tool call through the permission policy and registry."""

    tool = registry.get(tool_use.name)
    if tool is None:
        return ToolResultMessage(
            tool_use_id=tool_use.id,
            content=f"Unknown tool: {tool_use.name}",
            is_error=True,
        )

    decision = context.permission_policy.authorize(
        tool_name=tool.name,
        background=background,
    )
    if not decision.allowed:
        return ToolResultMessage(
            tool_use_id=tool_use.id,
            content=f"Permission denied for {tool.name}: {decision.reason}",
            is_error=True,
        )

    try:
        result = await tool.run(tool_use.input, context)
        return ToolResultMessage(
            tool_use_id=tool_use.id,
            content=result.content,
            is_error=result.is_error,
        )
    except Exception as exc:  # noqa: BLE001 - tool boundary
        return ToolResultMessage(
            tool_use_id=tool_use.id,
            content=f"{tool.name} failed: {exc}",
            is_error=True,
        )


async def run_query_loop(
    *,
    model_client: ModelClient,
    system_prompt: str,
    messages: Iterable[ConversationMessage],
    registry: ToolRegistry,
    context: ToolContext,
    model: str,
    max_turns: int,
    max_output_tokens: int,
    background: bool = False,
) -> QueryResult:
    """Drive the core agent loop until the assistant stops asking for tools."""

    conversation = list(messages)
    for turn_index in range(1, max_turns + 1):
        assistant_message = await model_client.create_assistant_message(
            system_prompt=system_prompt,
            messages=conversation,
            tools=registry.schemas(),
            model=model,
            max_output_tokens=max_output_tokens,
        )
        conversation.append(assistant_message)

        tool_uses = assistant_message.tool_uses
        if not tool_uses:
            return QueryResult(
                output_text=assistant_message.text or "(no text output)",
                messages=conversation,
                turns=turn_index,
            )

        for tool_use in tool_uses:
            tool_result = await execute_tool_use(
                tool_use,
                registry=registry,
                context=context,
                background=background,
            )
            conversation.append(tool_result)

    return QueryResult(
        output_text="Stopped after reaching the max turn limit.",
        messages=conversation,
        turns=max_turns,
    )
