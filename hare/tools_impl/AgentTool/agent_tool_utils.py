"""
Agent tool utilities.

Port of: src/tools/AgentTool/agentToolUtils.ts

Resolves which tools an agent has access to based on its definition.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from hare.tools_impl.AgentTool.built_in_agents import AgentDefinition


def resolve_agent_tools(
    agent_definition: AgentDefinition,
    all_tools: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Resolve the set of tools available to an agent based on its definition.

    If agent defines specific tools, only those are included.
    If agent defines disallowed tools, those are excluded from all tools.
    Otherwise, all tools are available.
    """
    allowed = agent_definition.tools
    disallowed = set(agent_definition.disallowed_tools)

    if allowed:
        allow_set = set(allowed)
        filtered = [t for t in all_tools if t.get("name") in allow_set]
    else:
        filtered = list(all_tools)

    if disallowed:
        filtered = [t for t in filtered if t.get("name") not in disallowed]

    return filtered


def get_agent_model(
    agent_definition: AgentDefinition,
    *,
    parent_model: str = "",
    requested_model: str = "",
) -> str:
    """Determine which model an agent should use."""
    if requested_model:
        return requested_model
    if agent_definition.model:
        return agent_definition.model
    return parent_model


def format_agent_line(agent: AgentDefinition) -> str:
    """Format one agent line for display."""
    tools_desc = _get_tools_description(agent)
    return f"- {agent.agent_type}: {agent.when_to_use} (Tools: {tools_desc})"


def _get_tools_description(agent: AgentDefinition) -> str:
    """Get a description of the tools available to an agent."""
    has_allowlist = bool(agent.tools)
    has_denylist = bool(agent.disallowed_tools)

    if has_allowlist and has_denylist:
        deny_set = set(agent.disallowed_tools)
        effective = [t for t in agent.tools if t not in deny_set]
        return ", ".join(effective) if effective else "None"
    elif has_allowlist:
        return ", ".join(agent.tools)
    elif has_denylist:
        return f"All tools except {', '.join(agent.disallowed_tools)}"
    return "All tools"
