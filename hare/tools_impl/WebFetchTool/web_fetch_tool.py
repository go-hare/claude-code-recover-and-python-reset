"""
WebFetchTool - fetch URL content.

Port of: src/tools/WebFetchTool/WebFetchTool.ts
"""

from __future__ import annotations

from typing import Any

WEB_FETCH_TOOL_NAME = "WebFetch"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"},
        },
        "required": ["url"],
    }


async def call(
    tool_input: dict[str, Any],
    **context: Any,
) -> dict[str, Any]:
    """Fetch a URL and return its content."""
    url = tool_input.get("url", "")
    if not url:
        return {"type": "error", "error": "url is required"}

    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Claude-CLI/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        if len(content) > 100_000:
            content = content[:100_000] + "\n\n[... truncated ...]"
        return {"type": "tool_result", "content": content, "is_error": False}
    except Exception as e:
        return {"type": "error", "error": f"Fetch failed: {e}"}
