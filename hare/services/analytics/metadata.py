"""
Analytics metadata utilities.

Port of: src/services/analytics/metadata.ts
"""

from __future__ import annotations

import platform
import time
from typing import Any, Optional


def build_event_metadata(
    *,
    session_id: str = "",
    agent_id: str = "",
    model: str = "",
    tool_name: str = "",
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build standardized metadata for an analytics event."""
    meta: dict[str, Any] = {
        "platform": platform.system().lower(),
        "timestamp": int(time.time() * 1000),
    }
    if session_id:
        meta["session_id"] = session_id
    if agent_id:
        meta["agent_id"] = agent_id
    if model:
        meta["model"] = model
    if tool_name:
        meta["tool_name"] = sanitize_tool_name_for_analytics(tool_name)
    if extra:
        meta.update(extra)
    return meta


def sanitize_tool_name_for_analytics(tool_name: str) -> str:
    """Sanitize tool name for analytics (remove sensitive info)."""
    # MCP tool names may contain server info
    if "/" in tool_name:
        parts = tool_name.split("/")
        return f"mcp/{parts[-1]}" if len(parts) > 1 else tool_name
    return tool_name
