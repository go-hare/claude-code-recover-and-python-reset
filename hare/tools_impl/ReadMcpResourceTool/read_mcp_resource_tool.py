"""
Read MCP Resource Tool.

Port of: src/tools/ReadMcpResourceTool/ReadMcpResourceTool.ts
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "ReadMcpResource"
DESCRIPTION = "Read an MCP resource by URI"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "server_name": {"type": "string", "description": "MCP server name"},
            "uri": {"type": "string", "description": "Resource URI"},
        },
        "required": ["server_name", "uri"],
    }


async def call(server_name: str, uri: str, **kwargs: Any) -> dict[str, Any]:
    return {"server": server_name, "uri": uri, "content": "", "status": "not_connected"}
