"""Port of: src/commands/outputStyle.ts"""
from __future__ import annotations
from typing import Any
from hare.constants.output_styles import get_all_output_styles, get_output_style_config

COMMAND_NAME = "output-style"
DESCRIPTION = "Set the output style (concise, explanatory, learning)"
ALIASES = ["style"]

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    style = args.strip().lower()
    if not style:
        styles = get_all_output_styles()
        return {"type": "output-style", "display_text": f"Available styles: {', '.join(styles)}"}
    config = get_output_style_config(style)
    if not config:
        return {"type": "error", "display_text": f"Unknown style: {style}. Use: {', '.join(get_all_output_styles())}"}
    return {"type": "output-style", "style": style, "display_text": f"Output style set to: {config.output_style_label}"}
