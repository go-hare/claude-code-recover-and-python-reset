from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from claude_code_py.engine.context import ToolContext
from claude_code_py.engine.models import ToolRunResult
from claude_code_py.tools.base import Tool


class AgentTool(Tool):
    name = "Agent"
    aliases = ("Task",)
    description = "Launch a new agent"
    input_schema = {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "A short (3-5 word) description of the task.",
            },
            "prompt": {
                "type": "string",
                "description": "The task for the agent to perform.",
            },
            "subagent_type": {
                "type": "string",
                "description": "The type of specialized agent to use for this task.",
            },
            "model": {
                "type": "string",
                "description": "Optional model override for this agent.",
            },
            "run_in_background": {
                "type": "boolean",
                "description": "Whether to run this agent in the background.",
            },
        },
        "required": ["prompt", "description"],
    }

    async def run(
        self,
        tool_input: Mapping[str, Any],
        context: ToolContext,
    ) -> ToolRunResult:
        prompt = str(tool_input["prompt"])
        description = str(tool_input["description"])
        background = bool(tool_input.get("run_in_background", False))

        if background:
            handle = context.agent_runner.spawn_subagent(
                prompt=prompt,
                description=description,
            )
            return ToolRunResult(
                content=(
                    f"Started background agent {handle.task_id} "
                    f"for: {handle.description}"
                )
            )

        result = await context.agent_runner.run_subagent(
            prompt=prompt,
            description=description,
        )
        return ToolRunResult(content=result.output_text)
