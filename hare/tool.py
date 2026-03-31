"""
Tool type definitions and utilities.

Port of: src/Tool.ts

The Tool type is the core abstraction for all tools in the system.
ToolUseContext carries per-turn state through the tool execution pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    Any,
    Awaitable,
    Callable,
    Optional,
    Protocol,
    Sequence,
    runtime_checkable,
)

from hare.types.command import Command
from hare.types.ids import AgentId
from hare.types.message import (
    AssistantMessage,
    AttachmentMessage,
    Message,
    ProgressMessage,
    SystemMessage,
    UserMessage,
)
from hare.types.permissions import (
    PermissionMode,
    PermissionResult,
    ToolPermissionContext,
    ToolPermissionRulesBySource,
)
from hare.types.tools import ToolProgressData


# ---------------------------------------------------------------------------
# ToolInputJSONSchema
# ---------------------------------------------------------------------------

ToolInputJSONSchema = dict[str, Any]


# ---------------------------------------------------------------------------
# QueryChainTracking
# ---------------------------------------------------------------------------


@dataclass
class QueryChainTracking:
    chain_id: str = ""
    depth: int = 0


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


@dataclass
class ValidationResultOK:
    result: bool = True


@dataclass
class ValidationResultError:
    result: bool = False
    message: str = ""
    error_code: int = 0


ValidationResult = ValidationResultOK | ValidationResultError


# ---------------------------------------------------------------------------
# ToolResult
# ---------------------------------------------------------------------------


@dataclass
class ToolResult:
    data: Any = None
    new_messages: list[Message] = field(default_factory=list)
    context_modifier: Optional[Callable[["ToolUseContext"], "ToolUseContext"]] = None
    mcp_meta: Optional[dict[str, Any]] = None


# ---------------------------------------------------------------------------
# ToolUseContext  (corresponds to ToolUseContext in Tool.ts)
# ---------------------------------------------------------------------------


@dataclass
class ToolUseContextOptions:
    commands: list[Command] = field(default_factory=list)
    debug: bool = False
    main_loop_model: str = ""
    tools: list[Tool] = field(default_factory=list)
    verbose: bool = False
    thinking_config: Optional[dict[str, Any]] = None
    mcp_clients: list[Any] = field(default_factory=list)
    mcp_resources: dict[str, list[Any]] = field(default_factory=dict)
    is_non_interactive_session: bool = False
    agent_definitions: Optional[dict[str, Any]] = None
    max_budget_usd: Optional[float] = None
    custom_system_prompt: Optional[str] = None
    append_system_prompt: Optional[str] = None
    query_source: Optional[str] = None
    refresh_tools: Optional[Callable[[], list["Tool"]]] = None
    theme: str = "default"
    ide_installation_status: Optional[str] = None


@dataclass
class ToolUseContext:
    """
    Context passed to tool.call() and through the query loop.

    Carries per-turn and per-session state: permission context, abort controller,
    file caches, and options (model, tools, thinking config, etc.).
    """
    options: ToolUseContextOptions = field(default_factory=ToolUseContextOptions)
    abort_controller: Optional[Any] = None  # asyncio event or similar
    read_file_state: dict[str, Any] = field(default_factory=dict)
    get_app_state: Optional[Callable[[], Any]] = None
    set_app_state: Optional[Callable[[Callable[[Any], Any]], None]] = None
    handle_elicitation: Optional[Callable[..., Any]] = None
    nested_memory_attachment_triggers: set[str] = field(default_factory=set)
    loaded_nested_memory_paths: set[str] = field(default_factory=set)
    dynamic_skill_dir_triggers: set[str] = field(default_factory=set)
    discovered_skill_names: set[str] = field(default_factory=set)
    set_in_progress_tool_use_ids: Optional[Callable] = None
    set_response_length: Optional[Callable] = None
    update_file_history_state: Optional[Callable] = None
    update_attribution_state: Optional[Callable] = None
    set_sdk_status: Optional[Callable] = None
    agent_id: Optional[AgentId] = None
    agent_type: Optional[str] = None
    messages: list[Message] = field(default_factory=list)
    query_tracking: Optional[QueryChainTracking] = None
    tool_use_id: Optional[str] = None
    content_replacement_state: Optional[dict[str, Any]] = None
    add_notification: Optional[Callable] = None


# ---------------------------------------------------------------------------
# CanUseToolFn  (permission check callback)
# ---------------------------------------------------------------------------

CanUseToolFn = Callable[
    [
        "Tool",          # tool
        dict[str, Any],  # input
        ToolUseContext,   # toolUseContext
        AssistantMessage, # assistantMessage
        str,             # toolUseID
        Optional[str],   # forceDecision
    ],
    Awaitable[PermissionResult],
]


# ---------------------------------------------------------------------------
# Tool Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class Tool(Protocol):
    """
    Core tool interface. Every tool must implement at minimum:
    name, call, prompt, input_schema, check_permissions,
    map_tool_result_to_tool_result_block_param.
    """

    name: str
    aliases: list[str]
    max_result_size_chars: int
    search_hint: str

    async def call(
        self,
        args: dict[str, Any],
        context: ToolUseContext,
        can_use_tool: CanUseToolFn,
        parent_message: AssistantMessage,
        on_progress: Optional[Callable] = None,
    ) -> ToolResult: ...

    async def description(
        self,
        input: dict[str, Any],
        options: dict[str, Any],
    ) -> str: ...

    def input_schema(self) -> dict[str, Any]: ...

    def is_enabled(self) -> bool: ...

    def is_read_only(self, input: dict[str, Any]) -> bool: ...

    def is_concurrency_safe(self, input: dict[str, Any]) -> bool: ...

    async def check_permissions(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> PermissionResult: ...

    async def prompt(self, options: dict[str, Any]) -> str: ...

    def user_facing_name(self, input: Optional[dict[str, Any]] = None) -> str: ...

    def to_auto_classifier_input(self, input: dict[str, Any]) -> Any: ...

    def map_tool_result_to_tool_result_block_param(
        self, content: Any, tool_use_id: str
    ) -> dict[str, Any]: ...


# Convenience alias matching TS `Tools = readonly Tool[]`
Tools = Sequence[Tool]


# ---------------------------------------------------------------------------
# Helpers (matching exports from Tool.ts)
# ---------------------------------------------------------------------------


def tool_matches_name(tool: Tool, name: str) -> bool:
    """Checks if a tool matches the given name (primary name or alias)."""
    return tool.name == name or name in (getattr(tool, "aliases", None) or [])


def find_tool_by_name(tools: Tools, name: str) -> Optional[Tool]:
    """Finds a tool by name or alias from a list of tools."""
    for t in tools:
        if tool_matches_name(t, name):
            return t
    return None


# ---------------------------------------------------------------------------
# getEmptyToolPermissionContext
# ---------------------------------------------------------------------------


def get_empty_tool_permission_context() -> ToolPermissionContext:
    return ToolPermissionContext(
        mode="default",
        additional_working_directories={},
        always_allow_rules={},
        always_deny_rules={},
        always_ask_rules={},
        is_bypass_permissions_mode_available=False,
    )


# ---------------------------------------------------------------------------
# buildTool  (fills defaults for commonly-stubbed methods)
# ---------------------------------------------------------------------------


class ToolBase:
    """
    Base class for tool implementations. Provides safe defaults matching
    buildTool() from the TS source:

    - is_enabled → True
    - is_concurrency_safe → False (assume not safe)
    - is_read_only → False (assume writes)
    - is_destructive → False
    - check_permissions → allow
    - to_auto_classifier_input → "" (skip classifier)
    - user_facing_name → self.name
    """

    name: str = ""
    aliases: list[str] = []
    search_hint: str = ""
    max_result_size_chars: int = 100_000

    def is_enabled(self) -> bool:
        return True

    def is_concurrency_safe(self, input: dict[str, Any]) -> bool:
        return False

    def is_read_only(self, input: dict[str, Any]) -> bool:
        return False

    def is_destructive(self, input: dict[str, Any]) -> bool:
        return False

    async def check_permissions(
        self, input: dict[str, Any], context: ToolUseContext
    ) -> PermissionResult:
        from hare.types.permissions import PermissionAllowDecision
        return PermissionAllowDecision(behavior="allow", updated_input=input)

    def to_auto_classifier_input(self, input: dict[str, Any]) -> Any:
        return ""

    def user_facing_name(self, input: Optional[dict[str, Any]] = None) -> str:
        return self.name

    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def description(self, input: dict[str, Any], options: dict[str, Any]) -> str:
        return ""

    async def prompt(self, options: dict[str, Any]) -> str:
        return ""

    def map_tool_result_to_tool_result_block_param(
        self, content: Any, tool_use_id: str
    ) -> dict[str, Any]:
        text = str(content) if content is not None else ""
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": text,
        }


def filter_tool_progress_messages(
    progress_messages: list[ProgressMessage],
) -> list[ProgressMessage]:
    """Filter out hook progress messages."""
    return [
        msg
        for msg in progress_messages
        if msg.data is None or msg.data.get("type") != "hook_progress"
    ]
