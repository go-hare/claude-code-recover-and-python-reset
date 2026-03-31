"""
List MCP Resources Tool.

Port of: src/tools/ListMcpResourcesTool/ListMcpResourcesTool.ts
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "ListMcpResources"
DESCRIPTION = "List available MCP resources from connected servers"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "server_name": {"type": "string", "description": "MCP server name (optional)"},
        },
    }


async def call(server_name: str = "", **kwargs: Any) -> dict[str, Any]:
    return {"resources": [], "server": server_name or "all"}
