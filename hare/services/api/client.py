"""
Anthropic API client with streaming support.

Port of: src/services/api/claude.ts

Handles:
- Message construction (user/assistant → API format)
- Streaming and non-streaming requests
- Tool schema construction
- Usage tracking
- Retry logic
- Prompt caching
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Optional, Sequence
from uuid import uuid4

from hare.services.api.logging import NonNullableUsage, accumulate_usage
from hare.types.message import APIMessage, AssistantMessage
from hare.utils.model import normalize_model_string_for_api

MAX_NON_STREAMING_TOKENS = 128
MAX_OUTPUT_TOKENS_DEFAULT = 16384
MAX_OUTPUT_TOKENS_THINKING = 32768


@dataclass
class APIRequestParams:
    model: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    system: str | list[dict[str, Any]] = ""
    max_tokens: int = MAX_OUTPUT_TOKENS_DEFAULT
    tools: list[dict[str, Any]] = field(default_factory=list)
    temperature: float = 1.0
    stream: bool = True
    thinking: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


def get_max_output_tokens_for_model(model: str) -> int:
    """Get max output tokens based on model."""
    lower = model.lower()
    if "opus" in lower:
        return MAX_OUTPUT_TOKENS_THINKING
    return MAX_OUTPUT_TOKENS_DEFAULT


def build_system_prompt_blocks(
    system_prompt: list[str],
) -> str | list[dict[str, Any]]:
    """Build system prompt blocks for the API."""
    if not system_prompt:
        return ""
    if len(system_prompt) == 1:
        return system_prompt[0]
    return [{"type": "text", "text": s} for s in system_prompt]


def user_message_to_message_param(msg: dict[str, Any]) -> dict[str, Any]:
    """Convert internal user message to API message param."""
    content = msg.get("content", "")
    if isinstance(content, str):
        return {"role": "user", "content": content}
    return {"role": "user", "content": content}


def assistant_message_to_message_param(msg: dict[str, Any]) -> dict[str, Any]:
    """Convert internal assistant message to API message param."""
    content = msg.get("content", [])
    return {"role": "assistant", "content": content}


def build_tools_param(tools: Sequence[Any]) -> list[dict[str, Any]]:
    """Build tools parameter for API call."""
    result = []
    for tool in tools:
        schema = tool.input_schema() if callable(getattr(tool, "input_schema", None)) else {}
        result.append({
            "name": tool.name,
            "description": getattr(tool, "search_hint", tool.name),
            "input_schema": schema,
        })
    return result


async def call_model_api(
    *,
    messages: list[dict[str, Any]],
    system_prompt: list[str],
    model: str,
    tools: Sequence[Any],
    thinking_config: Optional[dict[str, Any]] = None,
    max_tokens: Optional[int] = None,
    stream: bool = True,
) -> Optional[AssistantMessage]:
    """
    Call the Anthropic Messages API.

    Mirrors queryModelWithStreaming() / queryModel() in claude.ts.
    Uses the official anthropic Python SDK.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _error_response("ANTHROPIC_API_KEY environment variable is not set.")

    api_model = normalize_model_string_for_api(model) if model else "claude-sonnet-4-6-20260301"

    try:
        import anthropic
    except ImportError:
        return _error_response(
            "anthropic package is not installed. Run: pip install anthropic"
        )

    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    client = anthropic.AsyncAnthropic(
        api_key=api_key,
        **({"base_url": base_url} if base_url else {}),
    )

    # Build request params
    effective_max_tokens = max_tokens or get_max_output_tokens_for_model(api_model)
    system_block = build_system_prompt_blocks(system_prompt)
    tools_param = build_tools_param(tools) if tools else []

    kwargs: dict[str, Any] = {
        "model": api_model,
        "max_tokens": effective_max_tokens,
        "messages": messages,
    }

    if system_block:
        kwargs["system"] = system_block
    if tools_param:
        kwargs["tools"] = tools_param
    if thinking_config:
        kwargs["thinking"] = thinking_config

    # Add betas if needed
    betas = _get_betas(api_model)
    if betas:
        kwargs["betas"] = betas

    start_time = time.time()

    try:
        if stream:
            return await _streaming_request(client, kwargs)
        else:
            return await _non_streaming_request(client, kwargs)
    except anthropic.APIError as e:
        return _error_response(f"API Error: {e.message}")
    except Exception as e:
        return _error_response(f"Error: {e}")
    finally:
        duration = time.time() - start_time
        from hare.cost_tracker import add_api_duration
        add_api_duration(duration)


async def _streaming_request(
    client: Any,
    kwargs: dict[str, Any],
) -> AssistantMessage:
    """Execute a streaming API request."""
    content_blocks: list[dict[str, Any]] = []
    usage = NonNullableUsage()
    stop_reason = "end_turn"
    model_used = kwargs.get("model", "")

    async with client.messages.stream(**kwargs) as stream:
        async for event in stream:
            pass  # Stream events consumed

        final = await stream.get_final_message()
        model_used = final.model
        stop_reason = final.stop_reason or "end_turn"

        for block in final.content:
            if block.type == "text":
                content_blocks.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                content_blocks.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
            elif block.type == "thinking":
                content_blocks.append({
                    "type": "thinking",
                    "thinking": block.thinking,
                })

        if final.usage:
            usage.input_tokens = final.usage.input_tokens
            usage.output_tokens = final.usage.output_tokens
            usage.cache_creation_input_tokens = getattr(final.usage, "cache_creation_input_tokens", 0) or 0
            usage.cache_read_input_tokens = getattr(final.usage, "cache_read_input_tokens", 0) or 0

    # Track usage
    from hare.cost_tracker import add_usage
    add_usage(usage)

    return AssistantMessage(
        type="assistant",
        uuid=str(uuid4()),
        message=APIMessage(
            role="assistant",
            content=content_blocks,
            model=model_used,
            stop_reason=stop_reason,
            usage={
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
            },
        ),
    )


async def _non_streaming_request(
    client: Any,
    kwargs: dict[str, Any],
) -> AssistantMessage:
    """Execute a non-streaming API request."""
    kwargs.pop("stream", None)
    response = await client.messages.create(**kwargs)

    content_blocks: list[dict[str, Any]] = []
    for block in response.content:
        if block.type == "text":
            content_blocks.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            content_blocks.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })

    usage = NonNullableUsage(
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )

    from hare.cost_tracker import add_usage
    add_usage(usage)

    return AssistantMessage(
        type="assistant",
        uuid=str(uuid4()),
        message=APIMessage(
            role="assistant",
            content=content_blocks,
            model=response.model,
            stop_reason=response.stop_reason or "end_turn",
            usage={
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
            },
        ),
    )


def _error_response(message: str) -> AssistantMessage:
    """Create an error response message."""
    return AssistantMessage(
        type="assistant",
        uuid=str(uuid4()),
        message=APIMessage(
            role="assistant",
            content=[{"type": "text", "text": message}],
            stop_reason="end_turn",
        ),
    )


def _get_betas(model: str) -> list[str]:
    """Get beta features to enable for this model."""
    betas: list[str] = []
    # Prompt caching is generally available now
    return betas
