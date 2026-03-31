"""
WebSearchTool - search the web.

Port of: src/tools/WebSearchTool/WebSearchTool.ts
"""

from __future__ import annotations

from typing import Any

WEB_SEARCH_TOOL_NAME = "WebSearch"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
        },
        "required": ["query"],
    }


async def call(
    tool_input: dict[str, Any],
    **context: Any,
) -> dict[str, Any]:
    """Search the web. Uses Anthropic's built-in web search."""
    query = tool_input.get("query", "")
    if not query:
        return {"type": "error", "error": "query is required"}
    return {
        "type": "tool_result",
        "content": f"Web search for: {query}\n(Web search requires API server-side tool)",
        "is_error": False,
    }
