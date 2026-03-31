"""Port of: src/commands/vim.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "vim"
DESCRIPTION = "Toggle vim keybindings"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    return {"type": "vim", "display_text": "Vim mode toggled."}
