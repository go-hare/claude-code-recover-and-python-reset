"""
Command type definitions.

Port of: src/types/command.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Literal, Optional, Union


@dataclass
class PromptCommand:
    """A prompt-type command that generates text sent to the model."""
    type: Literal["prompt"] = "prompt"
    name: str = ""
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    source: str = "builtin"  # "builtin" | "plugin" | "bundled" | "mcp"
    loaded_from: Optional[str] = None  # "skills" | "plugin" | "bundled" | "commands_DEPRECATED" | "mcp"
    content_length: int = 0
    progress_message: str = ""
    disable_model_invocation: bool = False
    has_user_specified_description: bool = False
    when_to_use: Optional[str] = None
    kind: Optional[str] = None  # "workflow" etc.
    availability: Optional[list[str]] = None
    plugin_info: Optional[dict[str, Any]] = None
    is_enabled: Optional[Callable[[], bool]] = None

    async def get_prompt_for_command(
        self, args: str, context: dict[str, Any]
    ) -> str:
        return ""


@dataclass
class LocalCommand:
    """A local command that executes and returns text."""
    type: Literal["local"] = "local"
    name: str = ""
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    source: str = "builtin"
    availability: Optional[list[str]] = None
    is_enabled: Optional[Callable[[], bool]] = None

    async def call(self, args: str, context: dict[str, Any]) -> dict[str, Any]:
        return {"type": "text", "text": ""}


@dataclass
class LocalJSXCommand:
    """A local-jsx command (renders interactive UI in the terminal)."""
    type: Literal["local-jsx"] = "local-jsx"
    name: str = ""
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    source: str = "builtin"
    availability: Optional[list[str]] = None
    is_enabled: Optional[Callable[[], bool]] = None

    async def call(self, args: str, context: dict[str, Any]) -> dict[str, Any]:
        return {"type": "text", "text": ""}


Command = Union[PromptCommand, LocalCommand, LocalJSXCommand]


def get_command_name(cmd: Command) -> str:
    """Get the display name for a command (prefixed with /)."""
    return f"/{cmd.name}"


def is_command_enabled(cmd: Command) -> bool:
    """Check if a command is enabled."""
    if cmd.is_enabled is not None:
        return cmd.is_enabled()
    return True
