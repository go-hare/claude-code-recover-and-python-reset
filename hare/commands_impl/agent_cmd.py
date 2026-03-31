"""Port of: src/commands/agent.ts"""
from __future__ import annotations
from typing import Any
from hare.tools_impl.AgentTool.load_agents_dir import load_all_agent_definitions
from hare.tools_impl.AgentTool.agent_tool_utils import format_agent_line

COMMAND_NAME = "agent"
DESCRIPTION = "List available agents or get info about a specific agent"
ALIASES = ["agents"]

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    project_dir = context.get("project_dir", "")
    all_agents = load_all_agent_definitions(project_dir)
    if args.strip():
        target = args.strip()
        for agent in all_agents:
            if agent.agent_type == target:
                lines = [
                    f"Agent: {agent.agent_type}",
                    f"Source: {agent.source}",
                    f"When to use: {agent.when_to_use}",
                    f"Description: {agent.description}",
                    f"Tools: {', '.join(agent.tools) if agent.tools else 'All'}",
                ]
                if agent.disallowed_tools:
                    lines.append(f"Disallowed: {', '.join(agent.disallowed_tools)}")
                return {"type": "agent", "display_text": "\n".join(lines)}
        return {"type": "error", "display_text": f"Agent '{target}' not found."}
    lines = ["Available agents:"]
    for agent in all_agents:
        lines.append(format_agent_line(agent))
    return {"type": "agent", "display_text": "\n".join(lines)}
