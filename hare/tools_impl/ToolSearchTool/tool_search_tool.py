"""
Tool Search Tool - search for available tools by keyword.

Port of: src/tools/ToolSearchTool/ToolSearchTool.ts
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "ToolSearch"
DESCRIPTION = "Search for available tools by keyword or capability"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
        },
        "required": ["query"],
    }


async def call(query: str, **kwargs: Any) -> dict[str, Any]:
    from hare.tools import get_all_base_tools
    query_lower = query.lower()
    tools = get_all_base_tools()
    matches = [
        t for t in tools
        if query_lower in t.get("name", "").lower()
        or query_lower in t.get("description", "").lower()
    ]
    return {
        "query": query,
        "matches": [{"name": t["name"], "description": t.get("description", "")} for t in matches],
        "total": len(matches),
    }
