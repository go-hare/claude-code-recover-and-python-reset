"""
CLI handler for MCP subcommand.

Port of: src/cli/mcp.ts
"""

from __future__ import annotations

from typing import Any

from hare.services.mcp.config import get_mcp_config


async def handle_mcp_command(args: dict[str, Any]) -> None:
    """Handle the 'mcp' CLI subcommand."""
    action = args.get("action", "list")
    if action == "list":
        config = get_mcp_config()
        servers = config.get("servers", {})
        if not servers:
            print("No MCP servers configured.")
            return
        print("Configured MCP servers:")
        for name, cfg in servers.items():
            transport = cfg.get("transport", "unknown")
            print(f"  {name} ({transport})")
    elif action == "add":
        print("MCP server add not yet implemented.")
    elif action == "remove":
        name = args.get("name", "")
        if not name:
            print("Usage: mcp remove <name>")
            return
        print(f"MCP server '{name}' removal not yet implemented.")
    else:
        print(f"Unknown MCP action: {action}")
