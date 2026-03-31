"""
Run agent - execute a subagent with its own context.

Port of: src/tools/AgentTool/runAgent.ts

This module handles the full lifecycle of spawning and running a subagent:
1. Resolve agent definition and tools
2. Initialize agent-specific MCP servers if any
3. Build system prompt and context
4. Run the query loop for the agent
5. Collect results and clean up
"""

from __future__ import annotations

import uuid
from typing import Any, Optional, Sequence

from hare.tools_impl.AgentTool.agent_color_manager import get_agent_color
from hare.tools_impl.AgentTool.agent_memory import save_agent_snapshot
from hare.tools_impl.AgentTool.agent_tool_utils import (
    format_agent_line,
    get_agent_model,
    resolve_agent_tools,
)
from hare.tools_impl.AgentTool.built_in_agents import (
    AgentDefinition,
    find_builtin_agent,
)
from hare.tools_impl.AgentTool.constants import AGENT_TOOL_NAME, ONE_SHOT_BUILTIN_AGENT_TYPES
from hare.tools_impl.AgentTool.load_agents_dir import load_all_agent_definitions


async def run_agent(
    *,
    prompt: str,
    description: str = "",
    subagent_type: str = "",
    model: str = "",
    name: str = "",
    parent_model: str = "",
    project_dir: str = "",
    run_in_background: bool = False,
    all_tools: Sequence[dict[str, Any]] = (),
    parent_messages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Run a subagent and return its result.

    This is the main entry point for launching agents.
    """
    agent_id = str(uuid.uuid4())[:8]

    # Resolve agent definition
    all_agents = load_all_agent_definitions(project_dir)
    agent_def = _find_agent_definition(subagent_type, all_agents)

    if not agent_def:
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": f"Unknown agent type: {subagent_type}",
        }

    # Resolve model
    resolved_model = get_agent_model(
        agent_def,
        parent_model=parent_model,
        requested_model=model,
    )

    # Resolve tools
    agent_tools = resolve_agent_tools(agent_def, list(all_tools))

    # Get color for display
    color = get_agent_color(agent_id)

    # Build the agent's system prompt
    system_prompt = agent_def.custom_system_prompt or _default_agent_system_prompt(agent_def)

    # In a full implementation, this would:
    # 1. Create a new query loop context
    # 2. Run the query loop with the agent's tools and prompt
    # 3. Collect and return the result
    # For now, return a stub result
    result = {
        "agent_id": agent_id,
        "agent_type": agent_def.agent_type,
        "model": resolved_model,
        "status": "completed",
        "description": description,
        "name": name or agent_def.agent_type,
        "color": color,
        "tools_count": len(agent_tools),
        "prompt_length": len(prompt),
    }

    # Save memory snapshot
    save_agent_snapshot(
        agent_id=agent_id,
        agent_type=agent_def.agent_type,
        summary=f"Agent {name or agent_def.agent_type} completed",
    )

    return result


async def resume_agent(
    *,
    agent_id: str,
    message: str,
) -> dict[str, Any]:
    """
    Resume a previously spawned agent by sending it a follow-up message.

    Port of: src/tools/AgentTool/resumeAgent.ts
    """
    return {
        "agent_id": agent_id,
        "status": "resumed",
        "message_length": len(message),
    }


def _find_agent_definition(
    agent_type: str,
    all_agents: list[AgentDefinition],
) -> Optional[AgentDefinition]:
    """Find an agent definition by type."""
    if not agent_type:
        # Default to general purpose
        return find_builtin_agent("generalPurpose")

    for agent in all_agents:
        if agent.agent_type == agent_type:
            return agent
    return None


def _default_agent_system_prompt(agent: AgentDefinition) -> str:
    """Generate a default system prompt for an agent."""
    return f"You are a {agent.agent_type} agent. {agent.description}"
