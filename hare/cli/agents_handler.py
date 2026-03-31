"""
CLI handler for agents subcommand.

Port of: src/cli/agents.ts
"""

from __future__ import annotations

from typing import Any

from hare.tools_impl.AgentTool.load_agents_dir import load_all_agent_definitions
from hare.tools_impl.AgentTool.agent_tool_utils import format_agent_line


async def handle_agents_command(args: dict[str, Any]) -> None:
    """Handle the 'agents' CLI subcommand."""
    project_dir = args.get("project_dir", "")
    agents = load_all_agent_definitions(project_dir)
    print("Available agents:")
    for agent in agents:
        print(format_agent_line(agent))
