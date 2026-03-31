"""Port of: src/commands/feedback.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "feedback"
DESCRIPTION = "Send feedback about Claude"
ALIASES = ["bug"]

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    text = args.strip()
    if not text:
        return {"type": "error", "display_text": "Usage: /feedback <your feedback>"}
    return {"type": "feedback", "text": text, "display_text": f"Thank you for your feedback!"}
