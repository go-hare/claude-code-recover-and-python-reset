"""
/help command - show help and available commands.

Port of: src/commands/help/index.ts
"""

from __future__ import annotations

from typing import Any

COMMAND_NAME = "help"
DESCRIPTION = "Show help and available commands"


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /help command."""
    from hare.commands_impl import get_all_command_definitions

    commands = get_all_command_definitions()
    lines = ["Available commands:"]
    for cmd in sorted(commands, key=lambda c: c["name"]):
        name = cmd["name"]
        desc = cmd.get("description", "")
        aliases = cmd.get("aliases", [])
        alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
        lines.append(f"  /{name}{alias_str} - {desc}")

    lines.append("\nType /command to run a command. Type a message to chat with Claude.")
    return {"type": "text", "value": "\n".join(lines)}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "call": call,
    }
