"""
MCP utility functions.

Port of: src/services/mcp/utils.ts
"""

from __future__ import annotations

import re
from typing import Any

from hare.services.mcp.types import McpServerConfig, McpStdioServerConfig


def format_server_name(name: str) -> str:
    """Format an MCP server name for display."""
    return name.replace("_", " ").replace("-", " ").title()


def validate_server_config(config: dict[str, Any]) -> list[str]:
    """Validate an MCP server config and return list of errors."""
    errors = []
    transport = config.get("type", "stdio")

    if transport == "stdio":
        if not config.get("command"):
            errors.append("stdio transport requires a 'command' field")
    elif transport in ("sse", "http", "streamable-http"):
        url = config.get("url", "")
        if not url:
            errors.append(f"{transport} transport requires a 'url' field")
        elif not re.match(r'^https?://', url):
            errors.append(f"Invalid URL: {url}")
    else:
        errors.append(f"Unknown transport type: {transport}")

    return errors


def get_server_display_info(name: str, config: McpServerConfig) -> dict[str, str]:
    """Get display information for an MCP server."""
    info = {"name": name, "display_name": format_server_name(name)}

    if isinstance(config, McpStdioServerConfig):
        info["type"] = "stdio"
        info["command"] = config.command
        if config.args:
            info["args"] = " ".join(config.args)
    else:
        info["type"] = getattr(config, "type", "unknown")
        info["url"] = getattr(config, "url", "")

    return info


def sanitize_mcp_output(output: str, max_chars: int = 100_000) -> str:
    """Sanitize and truncate MCP tool output."""
    if len(output) > max_chars:
        truncated = output[:max_chars]
        return f"{truncated}\n\n[Output truncated at {max_chars} characters]"
    return output
