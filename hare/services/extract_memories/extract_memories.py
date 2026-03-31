"""
Extract memories from conversation.

Port of: src/services/extractMemories/extractMemories.ts
"""

from __future__ import annotations

from typing import Any


async def extract_memories(
    messages: list[dict[str, Any]],
    *,
    model: str = "",
    memory_path: str = "",
) -> list[str]:
    """
    Extract useful memories from conversation messages.

    In production, calls the API to identify important facts/preferences.
    Returns list of memory strings to save.
    """
    memories: list[str] = []

    for msg in messages:
        if msg.get("type") != "assistant":
            continue
        content = msg.get("message", {}).get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block["text"]
                    if "remember" in text.lower() or "note:" in text.lower():
                        memories.append(text[:500])

    return memories
