"""
Full messages utilities.

Port of: src/utils/messages.ts

Comprehensive message creation, manipulation, and normalization utilities.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Optional, Sequence

from hare.utils.format import format_tokens


def create_user_message(
    text: str,
    *,
    is_meta: bool = False,
    uuid_str: str = "",
) -> dict[str, Any]:
    """Create a user message."""
    return {
        "type": "user",
        "uuid": uuid_str or str(uuid.uuid4()),
        "is_meta": is_meta,
        "message": {
            "role": "user",
            "content": text,
        },
    }


def create_assistant_message(
    content: list[dict[str, Any]] | str,
    *,
    uuid_str: str = "",
) -> dict[str, Any]:
    """Create an assistant message."""
    if isinstance(content, str):
        content = [{"type": "text", "text": content}]
    return {
        "type": "assistant",
        "uuid": uuid_str or str(uuid.uuid4()),
        "message": {
            "role": "assistant",
            "content": content,
        },
    }


def create_system_message(text: str) -> dict[str, Any]:
    """Create a system message."""
    return {
        "type": "system",
        "message": {"role": "system", "content": text},
    }


def create_compact_boundary_message(
    summary: str = "",
    *,
    direction: str = "",
) -> dict[str, Any]:
    """Create a compact boundary message."""
    return {
        "type": "system_compact_boundary",
        "summary": summary,
        "direction": direction,
    }


def create_command_input_message(
    command: str,
    args: str = "",
    stdout: str = "",
) -> dict[str, Any]:
    """Create a system message for a local command."""
    return {
        "type": "system_local_command",
        "command": command,
        "args": args,
        "stdout": stdout,
    }


def is_compact_boundary_message(msg: dict[str, Any]) -> bool:
    return msg.get("type") == "system_compact_boundary"


def get_messages_after_compact_boundary(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Get messages after the last compact boundary."""
    for i in range(len(messages) - 1, -1, -1):
        if is_compact_boundary_message(messages[i]):
            return messages[i + 1:]
    return messages


def get_assistant_message_text(msg: dict[str, Any]) -> str:
    """Extract text content from an assistant message."""
    if msg.get("type") != "assistant":
        return ""
    content = msg.get("message", {}).get("content", [])
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block["text"])
        return "\n".join(parts)
    return ""


def get_last_assistant_message(
    messages: list[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """Get the last assistant message."""
    for msg in reversed(messages):
        if msg.get("type") == "assistant":
            return msg
    return None


def get_content_text(msg: dict[str, Any]) -> str:
    """Get text content from any message type."""
    content = msg.get("message", {}).get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            b.get("text", "") for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def normalize_messages_for_api(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize messages for API consumption."""
    normalized = []
    for msg in messages:
        msg_type = msg.get("type", "")
        if msg_type in ("user", "assistant"):
            normalized.append(msg["message"])
        elif msg_type == "system":
            normalized.append(msg["message"])
    return normalized


def derive_short_message_id(uuid_str: str) -> str:
    """Derive a short stable message ID from a UUID."""
    clean = uuid_str.replace("-", "")
    try:
        num = int(clean[:12], 16)
        return _base36(num)[:6]
    except ValueError:
        return clean[:6]


def _base36(n: int) -> str:
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    result = []
    while n:
        n, r = divmod(n, 36)
        result.append(chars[r])
    return "".join(reversed(result))


def with_memory_correction_hint(message: str) -> str:
    """Append a memory correction hint to a message."""
    hint = (
        "\n\nNote: The user's next message may contain a correction or preference. "
        "Pay close attention — if they explain what went wrong or how they'd prefer "
        "you to work, consider saving that to memory for future sessions."
    )
    return message + hint


def count_tool_uses(messages: list[dict[str, Any]]) -> int:
    """Count total tool uses across messages."""
    count = 0
    for msg in messages:
        if msg.get("type") != "assistant":
            continue
        content = msg.get("message", {}).get("content", [])
        if isinstance(content, list):
            count += sum(1 for b in content if isinstance(b, dict) and b.get("type") == "tool_use")
    return count


def strip_thinking_blocks(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip thinking blocks from assistant messages."""
    result = []
    for msg in messages:
        if msg.get("type") != "assistant":
            result.append(msg)
            continue
        content = msg.get("message", {}).get("content", [])
        if not isinstance(content, list):
            result.append(msg)
            continue
        new_content = [b for b in content if not (isinstance(b, dict) and b.get("type") in ("thinking", "redacted_thinking"))]
        result.append({**msg, "message": {**msg["message"], "content": new_content}})
    return result
