"""Port of: src/commands/theme.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "theme"
DESCRIPTION = "Change the display theme"
ALIASES: list[str] = []

THEMES = ["dark", "light", "system", "monokai", "solarized"]

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    theme = args.strip().lower()
    if not theme:
        return {"type": "theme", "display_text": f"Available themes: {', '.join(THEMES)}"}
    if theme not in THEMES:
        return {"type": "error", "display_text": f"Unknown theme. Available: {', '.join(THEMES)}"}
    return {"type": "theme", "theme": theme, "display_text": f"Theme set to: {theme}"}
