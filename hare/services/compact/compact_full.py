"""
Full compact system.

Port of: src/services/compact/compact.ts

Implements conversation compaction by summarizing older messages
to free up context window space.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from hare.services.token_estimation import estimate_tokens


POST_COMPACT_MAX_FILES_TO_RESTORE = 5
POST_COMPACT_TOKEN_BUDGET = 50_000
POST_COMPACT_MAX_TOKENS_PER_FILE = 5_000
POST_COMPACT_MAX_TOKENS_PER_SKILL = 5_000
POST_COMPACT_SKILLS_TOKEN_BUDGET = 25_000
MAX_COMPACT_STREAMING_RETRIES = 2

ERROR_MESSAGE_NOT_ENOUGH_MESSAGES = "Not enough messages to compact"
ERROR_MESSAGE_INCOMPLETE_RESPONSE = "Incomplete response during compaction"
ERROR_MESSAGE_USER_ABORT = "User aborted compaction"


@dataclass
class CompactionResult:
    """Result of a compaction operation."""
    new_messages: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    tokens_before: int = 0
    tokens_after: int = 0
    messages_removed: int = 0
    user_display_message: str = ""


def strip_images_from_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip image blocks from messages before compaction."""
    result = []
    for msg in messages:
        if msg.get("type") != "user":
            result.append(msg)
            continue
        content = msg.get("message", {}).get("content", [])
        if not isinstance(content, list):
            result.append(msg)
            continue
        new_content = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "image":
                new_content.append({"type": "text", "text": "[image]"})
            elif isinstance(block, dict) and block.get("type") == "document":
                new_content.append({"type": "text", "text": "[document]"})
            else:
                new_content.append(block)
        new_msg = {**msg, "message": {**msg.get("message", {}), "content": new_content}}
        result.append(new_msg)
    return result


def should_compact(
    messages: list[dict[str, Any]],
    *,
    max_tokens: int = 200_000,
    current_tokens: int = 0,
) -> bool:
    """Determine if messages should be compacted."""
    if current_tokens > 0:
        return current_tokens > max_tokens * 0.9
    total = sum(estimate_tokens(str(m)) for m in messages)
    return total > max_tokens * 0.9


def find_compaction_point(
    messages: list[dict[str, Any]],
    *,
    target_ratio: float = 0.5,
) -> int:
    """Find the optimal point to split messages for compaction."""
    if len(messages) <= 2:
        return 0
    target_idx = int(len(messages) * target_ratio)
    # Ensure we keep at least 2 messages
    return max(1, min(target_idx, len(messages) - 2))


async def compact_messages(
    messages: list[dict[str, Any]],
    *,
    custom_instructions: Optional[str] = None,
    max_tokens: int = 200_000,
) -> CompactionResult:
    """
    Compact a list of messages by summarizing older ones.

    In the full implementation, this would call the API to generate
    a summary. Currently uses a simplified local summary.
    """
    if len(messages) < 3:
        raise ValueError(ERROR_MESSAGE_NOT_ENOUGH_MESSAGES)

    stripped = strip_images_from_messages(messages)
    split_point = find_compaction_point(stripped)

    old_messages = stripped[:split_point]
    kept_messages = stripped[split_point:]

    summary_parts = []
    for msg in old_messages:
        msg_type = msg.get("type", "")
        content = msg.get("message", {}).get("content", "")
        if isinstance(content, str) and content:
            summary_parts.append(f"[{msg_type}] {content[:200]}")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    summary_parts.append(f"[{msg_type}] {block['text'][:200]}")

    summary = "Previous conversation summary:\n" + "\n".join(summary_parts[:20])

    summary_message = {
        "type": "system",
        "message": {"role": "system", "content": summary},
    }

    new_messages = [summary_message] + kept_messages

    return CompactionResult(
        new_messages=new_messages,
        summary=summary,
        tokens_before=sum(estimate_tokens(str(m)) for m in messages),
        tokens_after=sum(estimate_tokens(str(m)) for m in new_messages),
        messages_removed=len(old_messages),
    )


async def compact_conversation(
    messages: list[dict[str, Any]],
    context: Any = None,
    cache_params: Any = None,
    is_auto: bool = False,
    custom_instructions: str = "",
    is_partial: bool = False,
) -> CompactionResult:
    """Full conversation compaction (API-based in production)."""
    return await compact_messages(
        messages,
        custom_instructions=custom_instructions or None,
    )


def merge_hook_instructions(
    custom_instructions: str,
    hook_instructions: Optional[str],
) -> str:
    """Merge custom instructions with hook-provided instructions."""
    if not hook_instructions:
        return custom_instructions
    if not custom_instructions:
        return hook_instructions
    return f"{custom_instructions}\n\n{hook_instructions}"
