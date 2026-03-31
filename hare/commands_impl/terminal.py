"""Port of: src/commands/terminal.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "terminal"
DESCRIPTION = "Open or manage terminal sessions"
ALIASES = ["term"]

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    return {"type": "terminal", "display_text": "Terminal management handled by the runtime."}
