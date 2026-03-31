"""Port of: src/commands/context.ts"""
from __future__ import annotations
from typing import Any
from hare.services.token_estimation import estimate_tokens

COMMAND_NAME = "context"
DESCRIPTION = "Show current context window usage"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    total_text = ""
    for msg in messages:
        c = msg.get("message", {}).get("content", "")
        if isinstance(c, str):
            total_text += c
        elif isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") == "text":
                    total_text += b.get("text", "")
    tokens = estimate_tokens(total_text)
    max_ctx = 200_000
    pct = tokens / max_ctx * 100
    lines = [
        f"Context usage: ~{tokens:,} / {max_ctx:,} tokens ({pct:.1f}%)",
        f"Messages: {len(messages)}",
    ]
    return {"type": "context", "display_text": "\n".join(lines)}
