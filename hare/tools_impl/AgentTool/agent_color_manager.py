"""
Agent color manager - assign colors to agents for display.

Port of: src/tools/AgentTool/agentColorManager.ts
"""

from __future__ import annotations

AGENT_COLORS = [
    "cyan", "magenta", "yellow", "green", "blue", "red",
    "bright_cyan", "bright_magenta", "bright_yellow",
    "bright_green", "bright_blue", "bright_red",
]

_color_index = 0
_agent_colors: dict[str, str] = {}


def get_agent_color(agent_id: str) -> str:
    """Get or assign a color for an agent."""
    global _color_index
    if agent_id not in _agent_colors:
        _agent_colors[agent_id] = AGENT_COLORS[_color_index % len(AGENT_COLORS)]
        _color_index += 1
    return _agent_colors[agent_id]


def reset_agent_colors() -> None:
    """Reset all agent color assignments."""
    global _color_index
    _color_index = 0
    _agent_colors.clear()
