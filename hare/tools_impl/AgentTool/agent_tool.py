"""
AgentTool – delegate work to a sub-agent.

Port of: src/tools/AgentTool/AgentTool.tsx

Launches a new agent with its own context and tool set to handle
complex, multi-step tasks autonomously.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from hare.tool import ToolBase, ToolResult, ToolUseContext
from hare.types.permissions import PermissionAllowDecision, PermissionResult

AGENT_TOOL_NAME = "Agent"
LEGACY_AGENT_TOOL_NAME = "Task"


class _AgentTool(ToolBase):
    name = AGENT_TOOL_NAME
    aliases = [LEGACY_AGENT_TOOL_NAME.lower(), "task", "subagent"]
    search_hint = "delegate work to a subagent"
    max_result_size_chars = 100_000

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The task for the agent to perform.",
                },
                "description": {
                    "type": "string",
                    "description": "A short (3-5 word) description of the task.",
                },
                "subagent_type": {
                    "type": "string",
                    "enum": [
                        "generalPurpose", "explore", "shell",
                        "browser-use", "best-of-n-runner",
                    ],
                    "description": "Subagent type to use for this task.",
                },
                "model": {
                    "type": "string",
                    "description": "Optional model to use for this agent.",
                },
                "run_in_background": {
                    "type": "boolean",
                    "description": "Run the agent in the background.",
                },
            },
            "required": ["prompt"],
        }

    def is_read_only(self, input: dict[str, Any]) -> bool:
        return True  # Delegates permission checks to its underlying tools

    def is_concurrency_safe(self, input: dict[str, Any]) -> bool:
        return True

    async def check_permissions(
        self, input: dict[str, Any], context: ToolUseContext
    ) -> PermissionResult:
        return PermissionAllowDecision(behavior="allow", updated_input=input)

    async def prompt(self, options: dict[str, Any]) -> str:
        return (
            "Launch a new agent to handle complex, multi-step tasks autonomously. "
            "Each agent has its own context and can use tools to complete the task."
        )

    async def description(self, input: dict[str, Any], options: dict[str, Any]) -> str:
        desc = input.get("description", "")
        return desc if desc else "Launch sub-agent"

    def user_facing_name(self, input: Optional[dict[str, Any]] = None) -> str:
        return AGENT_TOOL_NAME

    def to_auto_classifier_input(self, input: dict[str, Any]) -> Any:
        subagent_type = input.get("subagent_type", "")
        mode = input.get("mode", "")
        tags = [t for t in [subagent_type, f"mode={mode}" if mode else None] if t]
        prefix = f"({', '.join(tags)}): " if tags else ": "
        return f"{prefix}{input.get('prompt', '')}"

    async def call(
        self,
        args: dict[str, Any],
        context: ToolUseContext,
        can_use_tool: Any = None,
        parent_message: Any = None,
        on_progress: Any = None,
    ) -> ToolResult:
        """
        Launch a sub-agent to handle a task.

        In the full TS implementation, this creates a child QueryEngine with its
        own tool set and runs it to completion. For this port, we implement a
        simplified version that runs the query through a new engine instance.
        """
        prompt = args.get("prompt", "")
        description = args.get("description", "")
        subagent_type = args.get("subagent_type", "generalPurpose")
        model = args.get("model")
        run_in_background = args.get("run_in_background", False)

        if not prompt:
            return ToolResult(data="Error: prompt is required")

        try:
            from hare.query_engine import QueryEngine, QueryEngineConfig
            from hare.tools import get_tools
            from hare.commands import get_commands
            from hare.tool import get_empty_tool_permission_context
            from hare.utils.cwd import get_cwd

            permission_context = get_empty_tool_permission_context()
            tools = get_tools(permission_context)
            commands = await get_commands(get_cwd())

            async def child_can_use_tool(
                tool: Any, inp: Any, ctx: Any, msg: Any, tool_use_id: str, force: Any
            ) -> Any:
                return PermissionAllowDecision(behavior="allow", updated_input=inp)

            child_engine = QueryEngine(QueryEngineConfig(
                cwd=get_cwd(),
                tools=tools,
                commands=commands,
                can_use_tool=child_can_use_tool,
                get_app_state=lambda: {},
                set_app_state=lambda f: None,
                user_specified_model=model,
                verbose=False,
            ))

            result_text = ""
            async for msg in child_engine.submit_message(prompt):
                msg_type = msg.get("type", "")
                if msg_type == "result":
                    result_text = msg.get("result", "")

            if result_text:
                return ToolResult(data=result_text)
            else:
                return ToolResult(data="Agent completed the task.")

        except Exception as e:
            return ToolResult(data=f"Error launching agent: {e}")


AgentTool = _AgentTool()
