from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, TypeAlias


@dataclass(slots=True)
class TextBlock:
    type: Literal["text"] = "text"
    text: str = ""


@dataclass(slots=True)
class ToolUseBlock:
    type: Literal["tool_use"] = "tool_use"
    id: str = ""
    name: str = ""
    input: dict[str, Any] = field(default_factory=dict)


AssistantBlock: TypeAlias = TextBlock | ToolUseBlock


@dataclass(slots=True)
class UserMessage:
    role: Literal["user"] = "user"
    content: str = ""
    is_meta: bool = False


@dataclass(slots=True)
class AssistantMessage:
    role: Literal["assistant"] = "assistant"
    blocks: list[AssistantBlock] = field(default_factory=list)
    request_id: str | None = None

    @property
    def text(self) -> str:
        return "\n".join(
            block.text for block in self.blocks if isinstance(block, TextBlock)
        )

    @property
    def tool_uses(self) -> list[ToolUseBlock]:
        return [
            block for block in self.blocks if isinstance(block, ToolUseBlock)
        ]


@dataclass(slots=True)
class ToolResultMessage:
    role: Literal["user"] = "user"
    tool_use_id: str = ""
    content: str = ""
    is_error: bool = False


ConversationMessage: TypeAlias = UserMessage | AssistantMessage | ToolResultMessage


@dataclass(slots=True)
class ToolSchema:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(slots=True)
class QueryResult:
    output_text: str
    messages: list[ConversationMessage]
    turns: int


@dataclass(slots=True)
class ToolRunResult:
    content: str
    is_error: bool = False
