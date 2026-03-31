"""Port of: src/commands/rewind.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "rewind"
DESCRIPTION = "Rewind the conversation by removing recent messages"
ALIASES = ["undo"]

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    try:
        count = int(args.strip()) if args.strip() else 1
    except ValueError:
        count = 1
    count = max(1, min(count, len(messages)))
    new_messages = messages[:-count] if count < len(messages) else []
    return {
        "type": "rewind",
        "messages_removed": count,
        "new_messages": new_messages,
        "display_text": f"Rewound {count} message(s)",
    }
