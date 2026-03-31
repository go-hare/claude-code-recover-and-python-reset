"""
SDK / entrypoint types.

Port of: src/entrypoints/agentSdkTypes.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class SDKOptions:
    model: str = ""
    max_turns: int = 100
    system_prompt: str = ""
    tools: list[dict[str, Any]] = field(default_factory=list)
    on_message: Optional[Callable[..., Any]] = None
    on_tool_use: Optional[Callable[..., Any]] = None
    on_error: Optional[Callable[..., Any]] = None


@dataclass
class SDKResult:
    messages: list[dict[str, Any]] = field(default_factory=list)
    stop_reason: str = ""
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)


@dataclass
class SDKAssistantMessageError:
    error_type: str = ""
    message: str = ""
    retryable: bool = False
