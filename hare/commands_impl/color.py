"""Port of: src/commands/color.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "color"
DESCRIPTION = "Change the output color theme"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    theme = args.strip() or "default"
    return {"type": "color", "theme": theme, "display_text": f"Color theme set to: {theme}"}
