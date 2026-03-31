"""Port of: src/commands/review.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "review"
DESCRIPTION = "Review recent changes or a specific diff"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    return {
        "type": "review",
        "display_text": "Submit changes for AI review. Use with /diff to see current changes.",
    }
