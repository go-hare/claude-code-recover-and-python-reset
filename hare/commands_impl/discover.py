"""Port of: src/commands/discover.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "discover"
DESCRIPTION = "Discover available features and commands"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    from hare.commands_impl import get_all_command_definitions
    cmds = get_all_command_definitions()
    lines = ["Available commands:"]
    for cmd in sorted(cmds, key=lambda c: c["name"]):
        aliases = ", ".join(cmd.get("aliases", []))
        alias_str = f" (aliases: {aliases})" if aliases else ""
        lines.append(f"  /{cmd['name']}{alias_str} - {cmd['description']}")
    return {"type": "discover", "display_text": "\n".join(lines)}
