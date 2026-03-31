"""
/permissions command - manage allow & deny tool permission rules.

Port of: src/commands/permissions/index.ts
"""

from __future__ import annotations

from typing import Any

COMMAND_NAME = "permissions"
DESCRIPTION = "Manage allow & deny tool permission rules"
ALIASES = ["allowed-tools"]


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /permissions command."""
    from hare.utils.settings.settings import get_settings

    settings = get_settings()
    allowed = settings.get("allowedTools", [])
    denied = settings.get("deniedTools", [])
    permissions = settings.get("permissions", [])

    lines = ["Permission Rules:"]

    if allowed:
        lines.append("\nAllowed tools:")
        for tool in allowed:
            lines.append(f"  + {tool}")

    if denied:
        lines.append("\nDenied tools:")
        for tool in denied:
            lines.append(f"  - {tool}")

    if permissions:
        lines.append("\nCustom rules:")
        for rule in permissions:
            prefix = "+" if rule.get("type") == "allow" else "-"
            lines.append(f"  {prefix} {rule.get('tool', '')} {rule.get('pattern', '')}")

    if not allowed and not denied and not permissions:
        lines.append("\nNo permission rules configured.")

    return {"type": "text", "value": "\n".join(lines)}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "aliases": ALIASES,
        "call": call,
    }
