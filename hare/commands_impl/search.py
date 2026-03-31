"""Port of: src/commands/search.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "search"
DESCRIPTION = "Search conversation history"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    query = args.strip().lower()
    if not query:
        return {"type": "error", "display_text": "Usage: /search <query>"}
    matches = []
    for i, msg in enumerate(messages):
        content = msg.get("message", {}).get("content", "")
        text = ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            text = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
        if query in text.lower():
            preview = text[:100].replace("\n", " ")
            matches.append(f"  [{i}] {msg.get('type', '?')}: {preview}...")
    if not matches:
        return {"type": "search", "display_text": f"No matches for '{query}'."}
    return {"type": "search", "display_text": f"Found {len(matches)} match(es):\n" + "\n".join(matches[:20])}
