"""
Session memory compaction.

Port of: src/services/compact/sessionMemoryCompact.ts

Uses session memory (CLAUDE.md) to perform lightweight compaction
without needing an API call for summarization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from hare.services.compact.micro_compact import estimate_message_tokens


@dataclass
class SessionMemoryCompactConfig:
    min_tokens: int = 10_000
    min_text_block_messages: int = 5
    max_tokens: int = 40_000


DEFAULT_SM_COMPACT_CONFIG = SessionMemoryCompactConfig()
_config = SessionMemoryCompactConfig()


def set_session_memory_compact_config(config: dict[str, int]) -> None:
    global _config
    _config = SessionMemoryCompactConfig(
        min_tokens=config.get("min_tokens", DEFAULT_SM_COMPACT_CONFIG.min_tokens),
        min_text_block_messages=config.get("min_text_block_messages", DEFAULT_SM_COMPACT_CONFIG.min_text_block_messages),
        max_tokens=config.get("max_tokens", DEFAULT_SM_COMPACT_CONFIG.max_tokens),
    )


def get_session_memory_compact_config() -> SessionMemoryCompactConfig:
    return _config


async def try_session_memory_compaction(
    messages: list[dict[str, Any]],
    agent_id: str = "",
) -> Optional[dict[str, Any]]:
    """
    Try to compact using session memory.

    Returns a CompactionResult-like dict if successful, None if not applicable.
    Session memory compaction works by keeping recent messages and injecting
    the session memory as context instead of summarizing.
    """
    if len(messages) < _config.min_text_block_messages:
        return None

    total_tokens = estimate_message_tokens(messages)
    if total_tokens < _config.min_tokens:
        return None

    # Find messages with text blocks to keep
    text_msg_indices = []
    for i, msg in enumerate(messages):
        if _has_text_blocks(msg):
            text_msg_indices.append(i)

    if len(text_msg_indices) < _config.min_text_block_messages:
        return None

    # Keep recent messages up to max_tokens
    keep_from = len(messages)
    running_tokens = 0
    for i in range(len(messages) - 1, -1, -1):
        msg_tokens = estimate_message_tokens([messages[i]])
        if running_tokens + msg_tokens > _config.max_tokens:
            break
        running_tokens += msg_tokens
        keep_from = i

    if keep_from == 0:
        return None

    kept = messages[keep_from:]
    removed_count = len(messages) - len(kept)

    return {
        "new_messages": kept,
        "summary": f"Session memory compaction: kept {len(kept)} of {len(messages)} messages",
        "tokens_before": total_tokens,
        "tokens_after": running_tokens,
        "messages_removed": removed_count,
    }


def _has_text_blocks(message: dict[str, Any]) -> bool:
    """Check if a message contains text blocks."""
    msg_type = message.get("type", "")
    if msg_type == "assistant":
        content = message.get("message", {}).get("content", [])
        if isinstance(content, list):
            return any(b.get("type") == "text" for b in content if isinstance(b, dict))
    if msg_type == "user":
        content = message.get("message", {}).get("content", "")
        if isinstance(content, str):
            return bool(content)
        if isinstance(content, list):
            return any(b.get("type") == "text" for b in content if isinstance(b, dict))
    return False
