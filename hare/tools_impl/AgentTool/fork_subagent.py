"""
Fork subagent - create a forked copy of the current agent.

Port of: src/tools/AgentTool/forkSubagent.ts

A fork inherits the parent's full conversation context, unlike
a fresh subagent which starts with zero context.
"""

from __future__ import annotations

import os
from typing import Any, Optional


def is_fork_subagent_enabled() -> bool:
    """Check if fork subagent feature is enabled."""
    return os.environ.get("CLAUDE_CODE_FORK_SUBAGENT", "").lower() in ("1", "true")


def should_fork(
    *,
    subagent_type: Optional[str] = None,
    fork_enabled: bool = False,
) -> bool:
    """Determine if a request should fork rather than spawn a fresh agent."""
    if not fork_enabled and not is_fork_subagent_enabled():
        return False
    # Fork when no subagent_type is specified (omitting type = fork yourself)
    return subagent_type is None or subagent_type == ""


def create_fork_context(
    parent_messages: list[dict[str, Any]],
    prompt: str,
    *,
    name: str = "",
) -> dict[str, Any]:
    """Create the context for a forked agent."""
    return {
        "messages": list(parent_messages),
        "prompt": prompt,
        "name": name,
        "is_fork": True,
    }
