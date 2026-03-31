"""
/mcp command - manage MCP servers.

Port of: src/commands/mcp/index.ts
"""

from __future__ import annotations

from typing import Any

from hare.services.mcp.config import get_mcp_config
from hare.services.mcp.utils import format_server_name

COMMAND_NAME = "mcp"
DESCRIPTION = "Manage MCP servers"


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /mcp command."""
    parts = args.strip().split(None, 1)
    action = parts[0] if parts else ""
    server_name = parts[1] if len(parts) > 1 else ""

    config = get_mcp_config()

    if action == "enable" and server_name:
        server = config.get_server(server_name)
        if server:
            server.enabled = True
            return {"type": "text", "value": f"Enabled MCP server: {format_server_name(server_name)}"}
        return {"type": "text", "value": f"MCP server '{server_name}' not found"}

    if action == "disable" and server_name:
        server = config.get_server(server_name)
        if server:
            server.enabled = False
            return {"type": "text", "value": f"Disabled MCP server: {format_server_name(server_name)}"}
        return {"type": "text", "value": f"MCP server '{server_name}' not found"}

    # Default: list servers
    lines = ["MCP Servers:"]
    if config.servers:
        for s in config.servers:
            status = "enabled" if s.enabled else "disabled"
            connected = " (connected)" if s.connected else ""
            lines.append(f"  {format_server_name(s.name)} [{status}]{connected}")
    else:
        lines.append("  No MCP servers configured.")
    lines.append("\nUsage: /mcp [enable|disable] <server-name>")

    return {"type": "text", "value": "\n".join(lines)}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "immediate": True,
        "argument_hint": "[enable|disable [server-name]]",
        "call": call,
    }
