"""
Hook types.

Port of: src/types/hooks.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Literal, Optional, Union

HookEvent = Literal[
    "pre_tool_use",
    "post_tool_use",
    "pre_compact",
    "post_compact",
    "user_prompt_submit",
    "session_start",
    "subagent_start",
    "stop",
]


@dataclass
class HookDefinition:
    event: HookEvent
    command: str = ""
    script: str = ""
    timeout: float = 30.0
    blocking: bool = True
    matcher: Optional[str] = None


@dataclass
class HookResult:
    success: bool = True
    output: str = ""
    error: str = ""
    should_block: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HookContext:
    event: HookEvent
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)
    tool_output: Any = None
    messages: list[dict[str, Any]] = field(default_factory=list)
    session_id: str = ""
    agent_id: str = ""
