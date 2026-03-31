"""
Load agent definitions from agents directory.

Port of: src/tools/AgentTool/loadAgentsDir.ts

Loads user-defined and plugin-provided agent definitions from
.claude/agents/ directories (markdown frontmatter format).
"""

from __future__ import annotations

import os
import re
from typing import Any, Optional

from hare.tools_impl.AgentTool.built_in_agents import (
    AgentDefinition,
    get_builtin_agent_definitions,
    is_builtin_agent,
)


def load_agents_dir(
    directory: str,
    source: str = "user",
) -> list[AgentDefinition]:
    """Load agent definitions from a directory of markdown files."""
    agents: list[AgentDefinition] = []
    if not os.path.isdir(directory):
        return agents

    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(directory, filename)
        try:
            agent = _parse_agent_file(filepath, source)
            if agent:
                agents.append(agent)
        except Exception:
            continue
    return agents


def load_all_agent_definitions(
    project_dir: str,
) -> list[AgentDefinition]:
    """Load all agent definitions from all sources."""
    agents = get_builtin_agent_definitions()

    # User agents (~/.claude/agents/)
    user_dir = os.path.join(os.path.expanduser("~"), ".claude", "agents")
    agents.extend(load_agents_dir(user_dir, source="user"))

    # Project agents (.claude/agents/)
    if project_dir:
        project_agents_dir = os.path.join(project_dir, ".claude", "agents")
        agents.extend(load_agents_dir(project_agents_dir, source="project"))

    # Deduplicate by agent_type (later definitions override earlier)
    seen: dict[str, AgentDefinition] = {}
    for agent in agents:
        seen[agent.agent_type] = agent
    return list(seen.values())


def _parse_agent_file(filepath: str, source: str) -> Optional[AgentDefinition]:
    """Parse a markdown agent definition file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract YAML frontmatter
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not frontmatter_match:
        return None

    frontmatter = frontmatter_match.group(1)
    body = content[frontmatter_match.end():]

    # Simple YAML-like parsing
    props: dict[str, Any] = {}
    for line in frontmatter.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                items = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
                props[key] = items
            elif value.lower() in ("true", "false"):
                props[key] = value.lower() == "true"
            else:
                props[key] = value.strip("'\"")

    agent_type = props.get("agentType") or props.get("name", "")
    if not agent_type:
        basename = os.path.basename(filepath)
        agent_type = basename.rsplit(".", 1)[0]

    return AgentDefinition(
        agent_type=agent_type,
        when_to_use=props.get("whenToUse", props.get("description", "")),
        description=props.get("description", ""),
        tools=props.get("tools", []),
        disallowed_tools=props.get("disallowedTools", []),
        model=props.get("model", ""),
        custom_system_prompt=body.strip(),
        source=source,
        mcp_servers=props.get("mcpServers", []),
    )
