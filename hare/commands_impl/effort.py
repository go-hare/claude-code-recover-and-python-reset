"""Port of: src/commands/effort.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "effort"
DESCRIPTION = "Set the effort level for responses (low, medium, high)"
ALIASES: list[str] = []

VALID_EFFORTS = {"low", "medium", "high"}

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    level = args.strip().lower()
    if level not in VALID_EFFORTS:
        return {"type": "error", "display_text": f"Usage: /effort <{' | '.join(sorted(VALID_EFFORTS))}>"}
    return {"type": "effort", "effort": level, "display_text": f"Effort level set to: {level}"}
