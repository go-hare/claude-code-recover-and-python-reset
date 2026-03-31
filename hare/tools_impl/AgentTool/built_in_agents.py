"""
Built-in agent definitions.

Port of: src/tools/AgentTool/builtInAgents.ts + built-in/*.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentDefinition:
    """Definition of an agent type."""
    agent_type: str
    when_to_use: str
    description: str = ""
    tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)
    model: str = ""
    custom_system_prompt: str = ""
    source: str = "built-in"
    mcp_servers: list[Any] = field(default_factory=list)


GENERAL_PURPOSE_AGENT = AgentDefinition(
    agent_type="generalPurpose",
    when_to_use="General-purpose agent for researching complex questions, searching for code, and executing multi-step tasks",
    description="General purpose agent with access to all tools",
)

EXPLORE_AGENT = AgentDefinition(
    agent_type="Explore",
    when_to_use="Fast agent specialized for exploring codebases. Use for quick file searches, keyword searches, or answering questions about the codebase",
    description="Lightweight read-only agent for codebase exploration",
    tools=["FileRead", "Glob", "Grep", "Bash", "LSP"],
    disallowed_tools=["FileEdit", "FileWrite", "NotebookEdit"],
)

PLAN_AGENT = AgentDefinition(
    agent_type="Plan",
    when_to_use="Use for creating implementation plans and design discussions",
    description="Planning agent that analyzes and designs before implementation",
    tools=["FileRead", "Glob", "Grep", "Bash", "LSP"],
    disallowed_tools=["FileEdit", "FileWrite", "NotebookEdit"],
)

VERIFICATION_AGENT = AgentDefinition(
    agent_type="verification",
    when_to_use="Use after making changes to verify correctness by running tests and checking for errors",
    description="Verification agent that checks code changes",
)

CODE_REVIEWER_AGENT = AgentDefinition(
    agent_type="code-reviewer",
    when_to_use="Use for reviewing code changes, checking for bugs, and suggesting improvements",
    description="Code review agent",
    tools=["FileRead", "Glob", "Grep", "Bash"],
    disallowed_tools=["FileEdit", "FileWrite"],
)

BUILTIN_AGENTS: list[AgentDefinition] = [
    GENERAL_PURPOSE_AGENT,
    EXPLORE_AGENT,
    PLAN_AGENT,
    VERIFICATION_AGENT,
    CODE_REVIEWER_AGENT,
]


def get_builtin_agent_definitions() -> list[AgentDefinition]:
    """Return all built-in agent definitions."""
    return list(BUILTIN_AGENTS)


def find_builtin_agent(agent_type: str) -> Optional[AgentDefinition]:
    """Find a built-in agent by type."""
    for agent in BUILTIN_AGENTS:
        if agent.agent_type == agent_type:
            return agent
    return None


def is_builtin_agent(agent_type: str) -> bool:
    """Check if an agent type is a built-in agent."""
    return any(a.agent_type == agent_type for a in BUILTIN_AGENTS)
