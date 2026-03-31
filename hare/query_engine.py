"""
QueryEngine owns the query lifecycle and session state for a conversation.

Port of: src/QueryEngine.ts

It extracts the core logic from ask() into a standalone class that can be
used by both the headless/SDK path and (in a future phase) the REPL.

One QueryEngine per conversation. Each submit_message() call starts a new
turn within the same conversation. State (messages, file cache, usage, etc.)
persists across turns.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Optional
from uuid import uuid4

from hare.bootstrap.state import get_session_id, is_session_persistence_disabled
from hare.commands import get_slash_command_tool_skills
from hare.cost_tracker import get_model_usage, get_total_api_duration, get_total_cost
from hare.query import query, QueryParams
from hare.services.api.logging import (
    EMPTY_USAGE,
    NonNullableUsage,
    accumulate_usage,
    update_usage,
)
from hare.tool import CanUseToolFn, Tool, ToolUseContext, ToolUseContextOptions, Tools
from hare.types.command import Command
from hare.types.message import (
    AssistantMessage,
    AttachmentMessage,
    Message,
    SystemMessage,
    UserMessage,
)
from hare.types.permissions import PermissionMode, ToolPermissionContext
from hare.utils.cwd import get_cwd, set_cwd
from hare.utils.messages import (
    SYNTHETIC_MESSAGES,
    count_tool_calls,
    create_user_message,
    get_messages_after_compact_boundary,
)


# ---------------------------------------------------------------------------
# QueryEngineConfig
# ---------------------------------------------------------------------------

@dataclass
class QueryEngineConfig:
    cwd: str = ""
    tools: list[Tool] = field(default_factory=list)
    commands: list[Command] = field(default_factory=list)
    mcp_clients: list[Any] = field(default_factory=list)
    agents: list[Any] = field(default_factory=list)
    can_use_tool: Optional[CanUseToolFn] = None
    get_app_state: Optional[Any] = None
    set_app_state: Optional[Any] = None
    initial_messages: Optional[list[Message]] = None
    read_file_cache: dict[str, Any] = field(default_factory=dict)
    custom_system_prompt: Optional[str] = None
    append_system_prompt: Optional[str] = None
    user_specified_model: Optional[str] = None
    fallback_model: Optional[str] = None
    thinking_config: Optional[dict[str, Any]] = None
    max_turns: Optional[int] = None
    max_budget_usd: Optional[float] = None
    task_budget: Optional[dict[str, float]] = None
    json_schema: Optional[dict[str, Any]] = None
    verbose: bool = False
    replay_user_messages: bool = False
    handle_elicitation: Optional[Any] = None
    include_partial_messages: bool = False
    set_sdk_status: Optional[Any] = None
    abort_controller: Optional[asyncio.Event] = None
    snip_replay: Optional[Any] = None


# ---------------------------------------------------------------------------
# SDKMessage types emitted by QueryEngine (simplified)
# ---------------------------------------------------------------------------

SDKMessage = dict[str, Any]


# ---------------------------------------------------------------------------
# QueryEngine
# ---------------------------------------------------------------------------

class QueryEngine:
    """
    QueryEngine owns the query lifecycle and session state for a conversation.

    Mirrors the TypeScript QueryEngine class in src/QueryEngine.ts.
    """

    def __init__(self, config: QueryEngineConfig) -> None:
        self._config = config
        self._mutable_messages: list[Message] = list(config.initial_messages or [])
        self._abort_controller = config.abort_controller or asyncio.Event()
        self._permission_denials: list[dict[str, Any]] = []
        self._total_usage = EMPTY_USAGE
        self._has_handled_orphaned_permission = False
        self._read_file_state: dict[str, Any] = dict(config.read_file_cache)
        self._discovered_skill_names: set[str] = set()
        self._loaded_nested_memory_paths: set[str] = set()

    async def submit_message(
        self,
        prompt: str | list[Any],
        *,
        uuid: Optional[str] = None,
        is_meta: bool = False,
    ) -> AsyncGenerator[SDKMessage, None]:
        """
        Submit a new user message and yield SDK messages as the model responds.

        Each call starts a new turn within the same conversation.
        """
        config = self._config
        cwd = config.cwd
        commands = config.commands
        tools = config.tools
        mcp_clients = config.mcp_clients
        verbose = config.verbose
        max_turns = config.max_turns
        max_budget_usd = config.max_budget_usd
        can_use_tool = config.can_use_tool
        agents = config.agents or []

        self._discovered_skill_names.clear()
        set_cwd(cwd)
        persist_session = not is_session_persistence_disabled()
        start_time = time.time()

        # Determine model
        main_loop_model = config.user_specified_model or "claude-sonnet-4-20250514"

        # Thinking config
        thinking_config = config.thinking_config or {"type": "adaptive"}

        # Build system prompt (simplified – full impl would call getSystemPrompt)
        system_prompt_parts: list[str] = []
        if config.custom_system_prompt is not None:
            system_prompt_parts.append(config.custom_system_prompt)
        if config.append_system_prompt:
            system_prompt_parts.append(config.append_system_prompt)

        system_prompt = system_prompt_parts

        # Build ToolUseContext
        tool_use_context = ToolUseContext(
            options=ToolUseContextOptions(
                commands=commands,
                debug=False,
                tools=tools,
                verbose=verbose,
                main_loop_model=main_loop_model,
                thinking_config=thinking_config,
                mcp_clients=mcp_clients,
                is_non_interactive_session=True,
                agent_definitions={"activeAgents": agents, "allAgents": []},
            ),
            read_file_state=self._read_file_state,
            get_app_state=config.get_app_state,
            set_app_state=config.set_app_state,
            messages=list(self._mutable_messages),
            discovered_skill_names=self._discovered_skill_names,
            loaded_nested_memory_paths=self._loaded_nested_memory_paths,
        )

        # Create user message and push
        if isinstance(prompt, str):
            user_msg = create_user_message(content=prompt)
        else:
            user_msg = create_user_message(content=prompt)
        if uuid:
            user_msg.uuid = uuid
        user_msg.is_meta = is_meta

        self._mutable_messages.append(user_msg)
        messages = list(self._mutable_messages)

        # Yield system init message
        yield {
            "type": "system",
            "subtype": "init",
            "session_id": get_session_id(),
            "tools": [t.name for t in tools],
            "model": main_loop_model,
        }

        # Load skills (cache-only in headless/SDK mode)
        skills = await get_slash_command_tool_skills(get_cwd())

        # Run query loop
        current_message_usage = EMPTY_USAGE
        turn_count = 1
        last_stop_reason: Optional[str] = None

        query_params = QueryParams(
            messages=messages,
            system_prompt=system_prompt,
            user_context={},
            system_context={},
            can_use_tool=can_use_tool,
            tool_use_context=tool_use_context,
            fallback_model=config.fallback_model,
            query_source="sdk",
            max_turns=max_turns,
        )

        async for message in query(query_params):
            msg_type = getattr(message, "type", None)

            if msg_type == "assistant":
                self._mutable_messages.append(message)
                yield self._normalize_message(message)

            elif msg_type == "user":
                self._mutable_messages.append(message)
                turn_count += 1
                yield self._normalize_message(message)

            elif msg_type == "progress":
                self._mutable_messages.append(message)
                yield self._normalize_message(message)

            elif msg_type == "stream_event":
                event = getattr(message, "event", {})
                event_type = event.get("type", "")
                if event_type == "message_start":
                    current_message_usage = EMPTY_USAGE
                    current_message_usage = update_usage(
                        current_message_usage, event.get("message", {}).get("usage")
                    )
                elif event_type == "message_delta":
                    current_message_usage = update_usage(
                        current_message_usage, event.get("usage")
                    )
                    delta = event.get("delta", {})
                    if delta.get("stop_reason"):
                        last_stop_reason = delta["stop_reason"]
                elif event_type == "message_stop":
                    self._total_usage = accumulate_usage(
                        self._total_usage, current_message_usage
                    )

            elif msg_type == "attachment":
                self._mutable_messages.append(message)
                attachment = getattr(message, "attachment", {})
                if attachment.get("type") == "max_turns_reached":
                    yield {
                        "type": "result",
                        "subtype": "error_max_turns",
                        "is_error": True,
                        "duration_ms": (time.time() - start_time) * 1000,
                        "num_turns": attachment.get("turnCount", turn_count),
                        "session_id": get_session_id(),
                        "total_cost_usd": get_total_cost(),
                        "usage": self._total_usage,
                        "uuid": str(uuid4()),
                    }
                    return

            elif msg_type == "system":
                self._mutable_messages.append(message)
                subtype = getattr(message, "subtype", "")
                if subtype == "compact_boundary":
                    yield {
                        "type": "system",
                        "subtype": "compact_boundary",
                        "session_id": get_session_id(),
                        "uuid": getattr(message, "uuid", ""),
                    }

            # Check USD budget
            if max_budget_usd is not None and get_total_cost() >= max_budget_usd:
                yield {
                    "type": "result",
                    "subtype": "error_max_budget_usd",
                    "is_error": True,
                    "duration_ms": (time.time() - start_time) * 1000,
                    "num_turns": turn_count,
                    "session_id": get_session_id(),
                    "total_cost_usd": get_total_cost(),
                    "usage": self._total_usage,
                    "uuid": str(uuid4()),
                }
                return

        # Extract text result from last assistant message
        text_result = ""
        is_api_error = False
        for msg in reversed(self._mutable_messages):
            if msg.type == "assistant":
                content = msg.message.content
                if isinstance(content, list) and content:
                    last_block = content[-1]
                    if isinstance(last_block, dict) and last_block.get("type") == "text":
                        text = last_block.get("text", "")
                        if text not in SYNTHETIC_MESSAGES:
                            text_result = text
                is_api_error = bool(msg.is_api_error_message)
                break

        yield {
            "type": "result",
            "subtype": "success",
            "is_error": is_api_error,
            "duration_ms": (time.time() - start_time) * 1000,
            "duration_api_ms": get_total_api_duration(),
            "num_turns": turn_count,
            "result": text_result,
            "stop_reason": last_stop_reason,
            "session_id": get_session_id(),
            "total_cost_usd": get_total_cost(),
            "usage": self._total_usage,
            "model_usage": get_model_usage(),
            "permission_denials": self._permission_denials,
            "uuid": str(uuid4()),
        }

    def _normalize_message(self, message: Message) -> SDKMessage:
        """Convert internal message to SDK-compatible dict."""
        return {
            "type": message.type,
            "uuid": getattr(message, "uuid", ""),
            "session_id": get_session_id(),
            "message": message,
        }

    def interrupt(self) -> None:
        """Abort the current query."""
        self._abort_controller.set()

    def get_messages(self) -> list[Message]:
        return list(self._mutable_messages)

    def get_read_file_state(self) -> dict[str, Any]:
        return self._read_file_state

    def get_session_id(self) -> str:
        return get_session_id()

    def set_model(self, model: str) -> None:
        self._config.user_specified_model = model


# ---------------------------------------------------------------------------
# ask()  – convenience wrapper around QueryEngine for one-shot usage
# ---------------------------------------------------------------------------

async def ask(
    *,
    commands: list[Command],
    prompt: str | list[Any],
    cwd: str,
    tools: list[Tool],
    mcp_clients: list[Any] | None = None,
    verbose: bool = False,
    can_use_tool: Optional[CanUseToolFn] = None,
    mutable_messages: list[Message] | None = None,
    get_app_state: Optional[Any] = None,
    set_app_state: Optional[Any] = None,
    custom_system_prompt: Optional[str] = None,
    append_system_prompt: Optional[str] = None,
    user_specified_model: Optional[str] = None,
    fallback_model: Optional[str] = None,
    thinking_config: Optional[dict[str, Any]] = None,
    max_turns: Optional[int] = None,
    max_budget_usd: Optional[float] = None,
    agents: list[Any] | None = None,
    **kwargs: Any,
) -> AsyncGenerator[SDKMessage, None]:
    """
    Sends a single prompt to the Claude API and returns the response.
    Assumes non-interactive usage – will not ask for permissions.

    Convenience wrapper around QueryEngine for one-shot usage.
    """
    engine = QueryEngine(
        QueryEngineConfig(
            cwd=cwd,
            tools=tools,
            commands=commands,
            mcp_clients=mcp_clients or [],
            agents=agents or [],
            can_use_tool=can_use_tool,
            get_app_state=get_app_state,
            set_app_state=set_app_state,
            initial_messages=mutable_messages or [],
            read_file_cache={},
            custom_system_prompt=custom_system_prompt,
            append_system_prompt=append_system_prompt,
            user_specified_model=user_specified_model,
            fallback_model=fallback_model,
            thinking_config=thinking_config,
            max_turns=max_turns,
            max_budget_usd=max_budget_usd,
            verbose=verbose,
        )
    )

    async for msg in engine.submit_message(prompt):
        yield msg
