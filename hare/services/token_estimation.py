"""
Token estimation.

Port of: src/services/tokenEstimation.ts

Estimates token counts for messages without calling the API.
"""

from __future__ import annotations

from typing import Any

# Approximate: ~4 characters per token for English text
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text string."""
    if not text:
        return 0
    return max(1, len(text) // CHARS_PER_TOKEN)


def estimate_message_tokens(message: dict[str, Any]) -> int:
    """Estimate tokens for a single message."""
    content = message.get("content", "")
    if isinstance(content, str):
        return estimate_tokens(content)

    total = 0
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    total += estimate_tokens(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    total += estimate_tokens(str(block.get("input", "")))
                    total += 20  # overhead for tool structure
                elif block.get("type") == "tool_result":
                    total += estimate_tokens(str(block.get("content", "")))
                elif block.get("type") == "image":
                    total += 1600  # approximate tokens for an image
                elif block.get("type") == "thinking":
                    total += estimate_tokens(block.get("thinking", ""))
    return total


def estimate_messages_tokens(messages: list[dict[str, Any]]) -> int:
    """Estimate total tokens for a list of messages."""
    total = 0
    for msg in messages:
        total += estimate_message_tokens(msg)
        total += 4  # per-message overhead
    return total


def estimate_system_prompt_tokens(system: str | list[dict[str, Any]]) -> int:
    """Estimate tokens for the system prompt."""
    if isinstance(system, str):
        return estimate_tokens(system)
    return sum(estimate_tokens(block.get("text", "")) for block in system)
