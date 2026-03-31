"""
Conversation compaction service.

Port of: src/services/compact/

Compacts conversation history when it gets too long by summarizing older messages.
"""

from __future__ import annotations

from typing import Any, Optional

from hare.services.token_estimation import estimate_messages_tokens

# Trigger compaction when context reaches this % of max
COMPACTION_THRESHOLD_RATIO = 0.8
MAX_CONTEXT_TOKENS = 200_000
SUMMARY_TARGET_TOKENS = 2_000


def should_compact(
    messages: list[dict[str, Any]],
    max_tokens: int = MAX_CONTEXT_TOKENS,
) -> bool:
    """Check if conversation should be compacted."""
    estimated = estimate_messages_tokens(messages)
    return estimated > max_tokens * COMPACTION_THRESHOLD_RATIO


def find_compaction_point(
    messages: list[dict[str, Any]],
    keep_recent: int = 4,
) -> int:
    """
    Find the index at which to split messages for compaction.
    Keeps the most recent messages intact.
    """
    if len(messages) <= keep_recent:
        return 0
    return len(messages) - keep_recent


async def compact_messages(
    messages: list[dict[str, Any]],
    *,
    model: str = "",
    system_prompt: str = "",
) -> list[dict[str, Any]]:
    """
    Compact a conversation by summarizing older messages.

    Returns a new message list with a summary message replacing old messages.
    """
    split_point = find_compaction_point(messages)
    if split_point <= 0:
        return messages

    old_messages = messages[:split_point]
    recent_messages = messages[split_point:]

    summary = _summarize_messages(old_messages)

    summary_message = {
        "role": "user",
        "content": f"[Conversation summary: {summary}]",
    }

    return [summary_message] + recent_messages


def _summarize_messages(messages: list[dict[str, Any]]) -> str:
    """Create a text summary of messages."""
    parts: list[str] = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if isinstance(content, str):
            text = content[:200]
        elif isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", "")[:100])
            text = " ".join(text_parts)[:200]
        else:
            text = str(content)[:200]
        parts.append(f"{role}: {text}")

    return " | ".join(parts)
