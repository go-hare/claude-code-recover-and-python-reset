"""
Message creation and normalization utilities.

Port of: src/utils/messages.ts
"""

from __future__ import annotations

from typing import Any, Optional, Sequence
from uuid import uuid4

from hare.types.message import (
    APIMessage,
    AssistantMessage,
    AttachmentMessage,
    Message,
    SystemMessage,
    ToolUseSummaryMessage,
    UserMessage,
)


# Set of synthetic message texts the system uses internally
SYNTHETIC_MESSAGES: set[str] = set()


def create_user_message(
    *,
    content: Any,
    is_meta: bool = False,
    tool_use_result: Optional[str] = None,
    source_tool_assistant_uuid: Optional[str] = None,
) -> UserMessage:
    """Create a UserMessage matching createUserMessage in TS."""
    return UserMessage(
        type="user",
        uuid=str(uuid4()),
        message=APIMessage(role="user", content=content),
        is_meta=is_meta,
        tool_use_result=tool_use_result,
        source_tool_assistant_uuid=source_tool_assistant_uuid,
    )


def create_user_interruption_message(*, tool_use: bool = False) -> UserMessage:
    """Create a user interruption message."""
    content = "[Request interrupted by user]"
    return create_user_message(content=content, is_meta=True)


def create_system_message(content: str, subtype: str = "info") -> SystemMessage:
    """Create a system message."""
    return SystemMessage(
        type="system",
        uuid=str(uuid4()),
        subtype=subtype,
        content=content,
    )


def create_assistant_api_error_message(
    *,
    content: str,
    error: Optional[str] = None,
) -> AssistantMessage:
    """Create a synthetic assistant message for API errors."""
    return AssistantMessage(
        type="assistant",
        uuid=str(uuid4()),
        message=APIMessage(
            role="assistant",
            content=[{"type": "text", "text": content}],
        ),
        is_api_error_message=True,
        api_error=error,
    )


def create_attachment_message(attachment: dict[str, Any]) -> AttachmentMessage:
    """Create an attachment message."""
    return AttachmentMessage(
        type="attachment",
        uuid=str(uuid4()),
        attachment=attachment,
    )


def create_tool_use_summary_message(
    summary: str, tool_use_ids: list[str]
) -> ToolUseSummaryMessage:
    return ToolUseSummaryMessage(
        type="tool_use_summary",
        uuid=str(uuid4()),
        summary=summary,
        preceding_tool_use_ids=tool_use_ids,
    )


def create_microcompact_boundary_message(
    trigger: str,
    tokens_freed: int,
    deleted_tokens: int,
    deleted_tool_ids: list[str],
    preserved_ids: list[str],
) -> SystemMessage:
    return SystemMessage(
        type="system",
        uuid=str(uuid4()),
        subtype="compact_boundary",
        content="",
        compact_metadata={
            "trigger": trigger,
            "tokensFreed": tokens_freed,
            "deletedTokens": deleted_tokens,
            "deletedToolIds": deleted_tool_ids,
        },
    )


def get_messages_after_compact_boundary(messages: list[Message]) -> list[Message]:
    """Return messages after the last compact boundary, or all messages if none."""
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if getattr(msg, "type", "") == "system" and getattr(msg, "subtype", "") == "compact_boundary":
            return messages[i:]
    return messages


def normalize_messages_for_api(
    messages: list[Message], tools: Sequence[Any]
) -> list[Message]:
    """Normalize messages for the API (filter system messages, etc.)."""
    return [m for m in messages if m.type in ("user", "assistant")]


def count_tool_calls(messages: list[Message], tool_name: str) -> int:
    """Count how many times a specific tool was called in the message list."""
    count = 0
    for msg in messages:
        if msg.type == "assistant" and isinstance(msg.message.content, list):
            for block in msg.message.content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    if block.get("name") == tool_name:
                        count += 1
    return count


def strip_signature_blocks(messages: list[Message]) -> list[Message]:
    """Strip thinking signature blocks from messages."""
    # Simplified – full implementation would strip protected-thinking blocks
    return messages
