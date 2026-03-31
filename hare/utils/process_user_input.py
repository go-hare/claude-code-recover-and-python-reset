"""
User input processing.

Port of: src/utils/processUserInput/processUserInput.ts

Handles parsing user input, detecting slash commands, and preparing
messages for the query engine.
"""

from __future__ import annotations

from typing import Any, Optional

from hare.types.command import Command
from hare.types.message import UserMessage
from hare.utils.messages import create_user_message


def process_user_input(
    input_text: str,
    commands: list[Command],
) -> dict[str, Any]:
    """
    Process raw user input into a structured result.

    Returns a dict with:
    - type: "command" | "message"
    - command: the command object (if type is "command")
    - message: the UserMessage (if type is "message")
    - args: command arguments (if type is "command")
    """
    stripped = input_text.strip()

    # Check for slash commands
    if stripped.startswith("/"):
        parts = stripped.split(maxsplit=1)
        cmd_name = parts[0][1:]  # Remove the /
        cmd_args = parts[1] if len(parts) > 1 else ""

        from hare.commands import find_command
        cmd = find_command(cmd_name, commands)

        if cmd:
            return {
                "type": "command",
                "command": cmd,
                "args": cmd_args,
                "raw": stripped,
            }

    # Regular message
    return {
        "type": "message",
        "message": create_user_message(content=stripped),
        "raw": stripped,
    }
