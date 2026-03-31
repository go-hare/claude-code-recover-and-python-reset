"""Port of: src/commands/export.ts"""
from __future__ import annotations
import json
from typing import Any

COMMAND_NAME = "export"
DESCRIPTION = "Export the current conversation to a file"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    path = args.strip() or "conversation.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, default=str)
        return {"type": "export", "path": path, "display_text": f"Conversation exported to {path}"}
    except Exception as e:
        return {"type": "error", "display_text": f"Export failed: {e}"}
