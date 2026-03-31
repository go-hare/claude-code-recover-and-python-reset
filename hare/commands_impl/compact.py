"""
/compact command - compact conversation history.

Port of: src/commands/compact/compact.ts + index.ts

Clears conversation history but keeps a summary in context.
"""

from __future__ import annotations

from typing import Any, Optional

from hare.services.compact import should_compact, compact_messages


COMMAND_NAME = "compact"
DESCRIPTION = "Clear conversation history but keep a summary in context"
ALIASES: list[str] = []
ARGUMENT_HINT = "<optional custom summarization instructions>"


async def call(
    args: str,
    messages: list[dict[str, Any]],
    **context: Any,
) -> dict[str, Any]:
    """Execute the /compact command."""
    if not messages:
        return {"type": "error", "value": "No messages to compact"}

    custom_instructions = args.strip() if args else None

    try:
        result = await compact_messages(
            messages,
            custom_instructions=custom_instructions,
        )
        return {
            "type": "compact",
            "compaction_result": result,
            "display_text": "Compacted conversation history",
        }
    except Exception as e:
        return {"type": "error", "value": f"Error during compaction: {e}"}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "argument_hint": ARGUMENT_HINT,
        "supports_non_interactive": True,
        "call": call,
    }
