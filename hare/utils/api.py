"""
API client utilities.

Port of: src/utils/api.ts

Handles API calls to the Anthropic API.
"""

from __future__ import annotations

import os
from typing import Any, AsyncGenerator, Optional


async def call_api(
    messages: list[dict[str, Any]],
    *,
    model: str,
    system_prompt: str = "",
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int = 16384,
    temperature: float = 1.0,
    stream: bool = True,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Call the Anthropic API.

    This is a simplified port that uses the anthropic Python SDK.
    In the TS source, this handles streaming, retries, and error handling.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        yield {
            "type": "error",
            "error": "ANTHROPIC_API_KEY environment variable is not set.",
        }
        return

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=api_key)

        # Strip [1m] suffix from model name for API
        from hare.utils.model import normalize_model_string_for_api
        api_model = normalize_model_string_for_api(model)

        kwargs: dict[str, Any] = {
            "model": api_model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt
        if tools:
            kwargs["tools"] = tools

        if stream:
            async with client.messages.stream(**kwargs) as stream_response:
                async for event in stream_response:
                    yield _convert_event(event)

                final_message = await stream_response.get_final_message()
                yield {
                    "type": "message",
                    "message": _convert_message(final_message),
                }
        else:
            message = await client.messages.create(**kwargs)
            yield {
                "type": "message",
                "message": _convert_message(message),
            }

    except ImportError:
        yield {
            "type": "error",
            "error": "anthropic package is not installed. Run: pip install anthropic",
        }
    except Exception as e:
        yield {
            "type": "error",
            "error": str(e),
        }


def _convert_event(event: Any) -> dict[str, Any]:
    """Convert an SDK streaming event to our internal format."""
    return {
        "type": "stream_event",
        "event": event,
    }


def _convert_message(message: Any) -> dict[str, Any]:
    """Convert an SDK message to our internal dict format."""
    content_blocks = []
    for block in message.content:
        if block.type == "text":
            content_blocks.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            content_blocks.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })

    return {
        "role": "assistant",
        "content": content_blocks,
        "model": message.model,
        "stop_reason": message.stop_reason,
        "usage": {
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
        },
    }
