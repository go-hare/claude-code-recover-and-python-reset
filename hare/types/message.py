"""
Message types used throughout the system.

Port of: src/types/message.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Union
from uuid import uuid4


@dataclass
class APIMessage:
    """Raw API message shape (role + content)."""
    role: Literal["user", "assistant"]
    content: Any  # str | list[ContentBlock]
    stop_reason: Optional[str] = None
    usage: Optional[dict[str, int]] = None


@dataclass
class UserMessage:
    """A user message in the conversation."""
    type: Literal["user"] = "user"
    uuid: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = ""
    message: APIMessage = field(default_factory=lambda: APIMessage(role="user", content=""))
    is_meta: bool = False
    tool_use_result: Optional[str] = None
    source_tool_assistant_uuid: Optional[str] = None
    is_compact_summary: bool = False
    is_visible_in_transcript_only: bool = False


@dataclass
class AssistantMessage:
    """An assistant message in the conversation."""
    type: Literal["assistant"] = "assistant"
    uuid: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = ""
    message: APIMessage = field(default_factory=lambda: APIMessage(role="assistant", content=""))
    cost_usd: float = 0.0
    duration_ms: float = 0.0
    is_api_error_message: bool = False
    api_error: Optional[str] = None


@dataclass
class SystemMessage:
    """A system message (compact boundary, API error, warning, etc.)."""
    type: Literal["system"] = "system"
    uuid: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = ""
    subtype: str = ""  # "compact_boundary", "api_error", "warning", "local_command", etc.
    content: str = ""
    compact_metadata: Optional[dict[str, Any]] = None
    retry_attempt: Optional[int] = None
    max_retries: Optional[int] = None
    retry_in_ms: Optional[int] = None
    error: Optional[Any] = None


@dataclass
class ProgressMessage:
    """A progress message from a tool execution."""
    type: Literal["progress"] = "progress"
    uuid: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = ""
    tool_use_id: str = ""
    data: Optional[dict[str, Any]] = None


@dataclass
class AttachmentMessage:
    """An attachment message (file changes, max turns, structured output, etc.)."""
    type: Literal["attachment"] = "attachment"
    uuid: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = ""
    attachment: dict[str, Any] = field(default_factory=dict)


@dataclass
class TombstoneMessage:
    """Tombstone message: control signal for removing messages."""
    type: Literal["tombstone"] = "tombstone"
    message: Optional[AssistantMessage] = None


@dataclass
class StreamEvent:
    """A streaming event from the API."""
    type: Literal["stream_event"] = "stream_event"
    event: dict[str, Any] = field(default_factory=dict)


@dataclass
class RequestStartEvent:
    """Signals the start of an API request."""
    type: Literal["stream_request_start"] = "stream_request_start"


@dataclass
class ToolUseSummaryMessage:
    """Summary of tool use operations."""
    type: Literal["tool_use_summary"] = "tool_use_summary"
    uuid: str = field(default_factory=lambda: str(uuid4()))
    summary: str = ""
    preceding_tool_use_ids: list[str] = field(default_factory=list)


# Union of all message types
Message = Union[
    UserMessage,
    AssistantMessage,
    SystemMessage,
    ProgressMessage,
    AttachmentMessage,
]

# All possible yielded items from query loop
QueryYield = Union[
    StreamEvent,
    RequestStartEvent,
    Message,
    TombstoneMessage,
    ToolUseSummaryMessage,
]
