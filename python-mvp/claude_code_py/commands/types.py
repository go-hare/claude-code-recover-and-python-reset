from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Awaitable, Callable, Literal, Protocol

if TYPE_CHECKING:
    from claude_code_py.engine.query_engine import QueryEngine
    from claude_code_py.sessions.storage import SessionStore
    from claude_code_py.tools.registry import ToolRegistry


@dataclass(slots=True)
class PromptCommandInvocation:
    prompt: str
    description: str
    context: Literal["inline", "fork"] = "inline"
    allowed_tools: list[str] | None = None


@dataclass(slots=True)
class LocalCommandResult:
    output: str
    should_exit: bool = False
    next_engine: "QueryEngine | None" = None


@dataclass(slots=True)
class PromptCommand:
    name: str
    description: str
    aliases: list[str] = field(default_factory=list)
    progress_message: str = "running"
    context: Literal["inline", "fork"] = "inline"
    allowed_tools: list[str] | None = None
    argument_hint: str | None = None
    source: Literal["builtin", "skills", "plugin"] = "skills"
    is_hidden: bool = False
    loader: Callable[[str], PromptCommandInvocation] | None = None

    def invoke(self, args: str) -> PromptCommandInvocation:
        if self.loader is None:
            raise ValueError(f"Command {self.name} has no loader")
        return self.loader(args)


@dataclass(slots=True)
class CommandEnvironment:
    engine: "QueryEngine"
    session_store: "SessionStore"
    tool_registry: "ToolRegistry"
    config_home: Path
    cwd: Path
    set_engine: Callable[["QueryEngine"], None]
    list_commands: Callable[[], list["BaseCommand"]]
    list_plugins: Callable[[], list[str]]
    list_skills: Callable[[], list[str]]


LocalCommandHandler = Callable[[str, CommandEnvironment], Awaitable[LocalCommandResult]]


@dataclass(slots=True)
class LocalCommand:
    name: str
    description: str
    handler: LocalCommandHandler
    aliases: list[str] = field(default_factory=list)
    argument_hint: str | None = None
    source: Literal["builtin", "plugin"] = "builtin"
    is_hidden: bool = False


BaseCommand = PromptCommand | LocalCommand
