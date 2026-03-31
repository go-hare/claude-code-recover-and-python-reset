"""
Shell command splitting and analysis.

Port of: src/utils/bash/commands.ts
"""

from __future__ import annotations

import re
import shlex
from typing import Optional


def split_command(command: str) -> list[str]:
    """
    Split a compound command into individual commands.
    Handles &&, ||, ; separators while respecting quotes.
    """
    commands: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    i = 0

    while i < len(command):
        ch = command[i]

        if ch == "\\" and i + 1 < len(command) and (in_double or not in_single):
            current.append(ch)
            current.append(command[i + 1])
            i += 2
            continue

        if ch == "'" and not in_double:
            in_single = not in_single
            current.append(ch)
        elif ch == '"' and not in_single:
            in_double = not in_double
            current.append(ch)
        elif not in_single and not in_double:
            # Check for && and ||
            if ch in ("&", "|") and i + 1 < len(command) and command[i + 1] == ch:
                cmd_str = "".join(current).strip()
                if cmd_str:
                    commands.append(cmd_str)
                current = []
                i += 2
                continue
            # Check for ;
            if ch == ";":
                cmd_str = "".join(current).strip()
                if cmd_str:
                    commands.append(cmd_str)
                current = []
                i += 1
                continue
            current.append(ch)
        else:
            current.append(ch)

        i += 1

    remainder = "".join(current).strip()
    if remainder:
        commands.append(remainder)

    return commands


def get_command_name(command: str) -> Optional[str]:
    """Extract the executable name from a command string."""
    stripped = command.strip()
    if not stripped:
        return None

    # Skip leading env vars
    while True:
        m = re.match(r"^[A-Za-z_][A-Za-z0-9_]*=\S*\s+", stripped)
        if not m:
            break
        stripped = stripped[m.end():]

    # Get first token
    try:
        tokens = shlex.split(stripped)
    except ValueError:
        tokens = stripped.split()

    return tokens[0] if tokens else None


def get_command_prefix(command: str) -> str:
    """Get the command prefix (first word) for permission matching."""
    name = get_command_name(command)
    return name or ""
