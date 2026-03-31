"""
MCP Tool - execute MCP (Model Context Protocol) server tools.

Port of: src/tools/MCPTool/MCPTool.ts

The MCP tool acts as a bridge to external tool servers. Each MCP server
registers its own tools, and MCPTool dispatches calls to them.
Name, description, and schema are overridden per-server at registration time.
"""

from __future__ import annotations

from typing import Any, Optional

TOOL_NAME = "mcp"
DESCRIPTION = "Execute an MCP tool"
MAX_RESULT_SIZE_CHARS = 100_000


async def call_mcp_tool(
    server_name: str,
    tool_name: str,
    arguments: dict[str, Any],
    *,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """
    Call an MCP tool on a connected server.

    In the full implementation, this would:
    1. Look up the MCP server connection by name
    2. Send a tools/call request via the MCP protocol
    3. Return the result

    Currently returns a stub since MCP server management is not yet ported.
    """
    return {
        "type": "tool_result",
        "content": f"MCP tool {server_name}/{tool_name} called with {arguments}",
        "is_error": False,
    }


def build_mcp_tool_definition(
    server_name: str,
    tool_name: str,
    description: str,
    input_schema: dict[str, Any],
) -> dict[str, Any]:
    """Build a tool definition dict for an MCP-provided tool."""
    return {
        "name": f"mcp__{server_name}__{tool_name}",
        "description": description,
        "input_schema": input_schema,
        "is_mcp": True,
        "server_name": server_name,
        "original_tool_name": tool_name,
    }


def check_mcp_permissions(
    server_name: str,
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Check permissions for an MCP tool call."""
    return {
        "behavior": "ask",
        "message": f"Allow MCP tool {server_name}/{tool_name}?",
    }
