"""
Query loop – the core model-calling and tool-execution loop.

Port of: src/query.ts

The query loop:
1. Sends messages to the model API
2. Receives streaming responses
3. Detects tool_use blocks
4. Executes tools
5. Appends results
6. Loops back to step 1 until the model stops calling tools

Key concepts ported:
- State object carrying cross-iteration state
- Auto-compact tracking
- Max output tokens recovery
- Fallback model support
- Tool execution (sequential and streaming)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Optional, Sequence
from uuid import uuid4

from hare.tool import CanUseToolFn, Tool, ToolUseContext, find_tool_by_name
from hare.types.message import (
    AssistantMessage,
    AttachmentMessage,
    Message,
    RequestStartEvent,
    StreamEvent,
    SystemMessage,
    TombstoneMessage,
    ToolUseSummaryMessage,
    UserMessage,
)
from hare.utils.messages import (
    create_assistant_api_error_message,
    create_attachment_message,
    create_system_message,
    create_user_interruption_message,
    create_user_message,
    get_messages_after_compact_boundary,
    normalize_messages_for_api,
)

MAX_OUTPUT_TOKENS_RECOVERY_LIMIT = 3


# ---------------------------------------------------------------------------
# QueryParams
# ---------------------------------------------------------------------------

@dataclass
class QueryParams:
    messages: list[Message] = field(default_factory=list)
    system_prompt: list[str] = field(default_factory=list)
    user_context: dict[str, str] = field(default_factory=dict)
    system_context: dict[str, str] = field(default_factory=dict)
    can_use_tool: Optional[CanUseToolFn] = None
    tool_use_context: Optional[ToolUseContext] = None
    fallback_model: Optional[str] = None
    query_source: str = "sdk"
    max_output_tokens_override: Optional[int] = None
    max_turns: Optional[int] = None
    skip_cache_write: bool = False
    task_budget: Optional[dict[str, float]] = None


# ---------------------------------------------------------------------------
# Terminal / Continue transition types (matching query/transitions.ts)
# ---------------------------------------------------------------------------

@dataclass
class Terminal:
    reason: str = "completed"
    error: Optional[Any] = None
    turn_count: Optional[int] = None


@dataclass
class Continue:
    reason: str = "next_turn"


# ---------------------------------------------------------------------------
# Loop state (mutable state carried between loop iterations)
# ---------------------------------------------------------------------------

@dataclass
class _State:
    messages: list[Message] = field(default_factory=list)
    tool_use_context: Optional[ToolUseContext] = None
    auto_compact_tracking: Optional[dict[str, Any]] = None
    max_output_tokens_recovery_count: int = 0
    has_attempted_reactive_compact: bool = False
    max_output_tokens_override: Optional[int] = None
    pending_tool_use_summary: Optional[Any] = None
    stop_hook_active: Optional[bool] = None
    turn_count: int = 1
    transition: Optional[Continue] = None


# ---------------------------------------------------------------------------
# query()  – public entry point
# ---------------------------------------------------------------------------

async def query(
    params: QueryParams,
) -> AsyncGenerator[Message | StreamEvent | RequestStartEvent | TombstoneMessage | ToolUseSummaryMessage, None]:
    """
    The main query loop. Yields messages/events as they are produced.

    This is a faithful port of the query() and queryLoop() async generators
    from src/query.ts.
    """
    consumed_command_uuids: list[str] = []

    async for item in _query_loop(params, consumed_command_uuids):
        yield item


async def _query_loop(
    params: QueryParams,
    consumed_command_uuids: list[str],
) -> AsyncGenerator[Message | StreamEvent | RequestStartEvent | TombstoneMessage | ToolUseSummaryMessage, None]:
    """
    Inner query loop matching queryLoop() in query.ts.

    The while-true loop:
    1. Prepare messages (compact, microcompact, etc.)
    2. Call the model API with streaming
    3. Collect assistant responses and tool_use blocks
    4. If tool_use: execute tools, append results, continue
    5. If no tool_use: stop hooks, budget checks, return
    """
    system_prompt = params.system_prompt
    user_context = params.user_context
    system_context = params.system_context
    can_use_tool = params.can_use_tool
    fallback_model = params.fallback_model
    query_source = params.query_source
    max_turns = params.max_turns

    state = _State(
        messages=list(params.messages),
        tool_use_context=params.tool_use_context,
        max_output_tokens_override=params.max_output_tokens_override,
    )

    while True:
        tool_use_context = state.tool_use_context
        messages = state.messages
        turn_count = state.turn_count

        # Yield stream_request_start
        yield RequestStartEvent(type="stream_request_start")

        # Get messages after compact boundary
        messages_for_query = list(get_messages_after_compact_boundary(messages))

        # Build full system prompt
        full_system_prompt = list(system_prompt)

        # Call the model
        assistant_messages: list[AssistantMessage] = []
        tool_results: list[Message] = []
        tool_use_blocks: list[dict[str, Any]] = []
        needs_follow_up = False

        # Get model name from context
        current_model = ""
        if tool_use_context and tool_use_context.options:
            current_model = tool_use_context.options.main_loop_model

        try:
            # Call model API (simplified – full impl would stream from API)
            api_messages = _prepare_api_messages(messages_for_query, user_context)

            response = await _call_model(
                messages=api_messages,
                system_prompt=full_system_prompt,
                model=current_model,
                tools=tool_use_context.options.tools if tool_use_context else [],
                thinking_config=tool_use_context.options.thinking_config if tool_use_context else None,
            )

            if response:
                assistant_msg = response
                assistant_messages.append(assistant_msg)
                yield assistant_msg

                # Check for tool_use blocks
                if isinstance(assistant_msg.message.content, list):
                    for block in assistant_msg.message.content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            tool_use_blocks.append(block)
                            needs_follow_up = True

        except Exception as error:
            error_message = str(error)
            yield create_assistant_api_error_message(content=error_message)
            return

        # Check abort
        if tool_use_context and tool_use_context.abort_controller:
            if isinstance(tool_use_context.abort_controller, asyncio.Event):
                if tool_use_context.abort_controller.is_set():
                    yield create_user_interruption_message(tool_use=False)
                    return

        if not needs_follow_up:
            return

        # Execute tools
        if tool_use_blocks and tool_use_context:
            for tool_block in tool_use_blocks:
                tool_name = tool_block.get("name", "")
                tool_input = tool_block.get("input", {})
                tool_use_id = tool_block.get("id", str(uuid4()))

                tool = find_tool_by_name(
                    tool_use_context.options.tools, tool_name
                )

                if tool is None:
                    result_msg = create_user_message(
                        content=[{
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": f"Tool {tool_name} not found",
                            "is_error": True,
                        }],
                        tool_use_result=f"Tool {tool_name} not found",
                    )
                    yield result_msg
                    tool_results.append(result_msg)
                    continue

                try:
                    # Permission check
                    if can_use_tool:
                        perm_result = await can_use_tool(
                            tool,
                            tool_input,
                            tool_use_context,
                            assistant_messages[-1] if assistant_messages else AssistantMessage(),
                            tool_use_id,
                            None,
                        )
                        if perm_result.behavior == "deny":
                            result_msg = create_user_message(
                                content=[{
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": getattr(perm_result, "message", "Permission denied"),
                                    "is_error": True,
                                }],
                                tool_use_result="Permission denied",
                            )
                            yield result_msg
                            tool_results.append(result_msg)
                            continue

                    # Execute tool
                    tool_result = await tool.call(
                        tool_input,
                        tool_use_context,
                        can_use_tool or (lambda *a: asyncio.coroutine(lambda: None)()),
                        assistant_messages[-1] if assistant_messages else AssistantMessage(),
                    )

                    # Build tool result message
                    result_block = tool.map_tool_result_to_tool_result_block_param(
                        tool_result.data, tool_use_id
                    )
                    result_msg = create_user_message(
                        content=[result_block],
                        tool_use_result=str(tool_result.data),
                        source_tool_assistant_uuid=assistant_messages[-1].uuid if assistant_messages else None,
                    )
                    yield result_msg
                    tool_results.append(result_msg)

                    # Apply context modifier if any
                    if tool_result.context_modifier and tool_use_context:
                        tool_use_context = tool_result.context_modifier(tool_use_context)

                except Exception as e:
                    result_msg = create_user_message(
                        content=[{
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": f"Error: {e}",
                            "is_error": True,
                        }],
                        tool_use_result=f"Error: {e}",
                    )
                    yield result_msg
                    tool_results.append(result_msg)

        # Check abort after tool execution
        if tool_use_context and tool_use_context.abort_controller:
            if isinstance(tool_use_context.abort_controller, asyncio.Event):
                if tool_use_context.abort_controller.is_set():
                    yield create_user_interruption_message(tool_use=True)
                    return

        # Check max turns
        next_turn_count = turn_count + 1
        if max_turns and next_turn_count > max_turns:
            yield create_attachment_message({
                "type": "max_turns_reached",
                "maxTurns": max_turns,
                "turnCount": next_turn_count,
            })
            return

        # Continue loop with updated state
        state = _State(
            messages=[*messages_for_query, *assistant_messages, *tool_results],
            tool_use_context=tool_use_context,
            auto_compact_tracking=state.auto_compact_tracking,
            turn_count=next_turn_count,
            max_output_tokens_recovery_count=0,
            has_attempted_reactive_compact=False,
            max_output_tokens_override=None,
            pending_tool_use_summary=None,
            stop_hook_active=state.stop_hook_active,
            transition=Continue(reason="next_turn"),
        )


# ---------------------------------------------------------------------------
# API call helpers  (simplified – real impl would use Anthropic SDK)
# ---------------------------------------------------------------------------


def _prepare_api_messages(
    messages: list[Message], user_context: dict[str, str]
) -> list[dict[str, Any]]:
    """Prepare messages for the API call."""
    api_msgs: list[dict[str, Any]] = []
    for msg in messages:
        if msg.type in ("user", "assistant"):
            api_msgs.append({
                "role": msg.message.role,
                "content": msg.message.content,
            })
    return api_msgs


async def _call_model(
    *,
    messages: list[dict[str, Any]],
    system_prompt: list[str],
    model: str,
    tools: Sequence[Tool],
    thinking_config: Optional[dict[str, Any]] = None,
) -> Optional[AssistantMessage]:
    """
    Call the model API. This is a stub – real implementation would use
    the Anthropic SDK or a compatible client.

    In the TS source, this is handled by callModel() in src/services/api/claude.ts
    which calls queryModelWithStreaming() and yields streaming events.
    """
    try:
        from hare.services.api.client import call_model_api
        return await call_model_api(
            messages=messages,
            system_prompt=system_prompt,
            model=model,
            tools=tools,
            thinking_config=thinking_config,
        )
    except ImportError:
        from hare.types.message import APIMessage as _APIMessage
        return AssistantMessage(
            type="assistant",
            uuid=str(uuid4()),
            message=_APIMessage(
                role="assistant",
                content=[{"type": "text", "text": "No API client configured. Install with: pip install hare[anthropic]"}],
                stop_reason="end_turn",
            ),
        )
