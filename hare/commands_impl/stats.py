"""Port of: src/commands/stats.ts"""
from __future__ import annotations
from typing import Any
from hare.services.token_estimation import estimate_tokens

COMMAND_NAME = "stats"
DESCRIPTION = "Show conversation statistics"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    total = len(messages)
    user_count = sum(1 for m in messages if m.get("type") == "user")
    assistant_count = sum(1 for m in messages if m.get("type") == "assistant")
    tool_uses = 0
    for msg in messages:
        content = msg.get("message", {}).get("content", [])
        if isinstance(content, list):
            tool_uses += sum(1 for b in content if isinstance(b, dict) and b.get("type") == "tool_use")
    total_text = ""
    for msg in messages:
        content = msg.get("message", {}).get("content", "")
        if isinstance(content, str):
            total_text += content
        elif isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "text":
                    total_text += b.get("text", "")
    est_tokens = estimate_tokens(total_text)
    lines = [
        f"Messages: {total} ({user_count} user, {assistant_count} assistant)",
        f"Tool uses: {tool_uses}",
        f"Estimated tokens: {est_tokens:,}",
    ]
    display = "\n".join(lines)
    return {"type": "stats", "display_text": display, "stats": {
        "total": total, "user": user_count, "assistant": assistant_count,
        "tool_uses": tool_uses, "est_tokens": est_tokens,
    }}
