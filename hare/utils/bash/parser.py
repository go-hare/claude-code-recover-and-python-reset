"""
Shell command parser.

Port of: src/utils/bash/parser.ts, bashParser.ts, ParsedCommand.ts

Parses shell command strings into structured representations for
permission checking and analysis.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedCommand:
    """A parsed shell command."""
    raw: str = ""
    executable: str = ""
    args: list[str] = field(default_factory=list)
    is_piped: bool = False
    is_background: bool = False
    pipe_chain: list["ParsedCommand"] = field(default_factory=list)
    redirects: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)


def parse_command(command: str) -> ParsedCommand:
    """
    Parse a shell command string into a ParsedCommand.

    Handles:
    - Simple commands: git status
    - Pipes: cat file | grep pattern
    - Background: command &
    - Redirects: command > output.txt
    - Environment variables: FOO=bar command
    - Semicolons and &&
    """
    command = command.strip()
    if not command:
        return ParsedCommand(raw=command)

    # Check for pipes
    if "|" in command and not _is_in_quotes(command, command.index("|")):
        parts = _split_on_pipe(command)
        if len(parts) > 1:
            parsed_parts = [parse_command(p.strip()) for p in parts]
            first = parsed_parts[0]
            first.is_piped = True
            first.pipe_chain = parsed_parts[1:]
            return first

    # Check for background
    is_bg = command.rstrip().endswith("&")
    if is_bg:
        command = command.rstrip()[:-1].rstrip()

    # Parse environment variables
    env_vars: dict[str, str] = {}
    remaining = command
    while True:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(\S*)\s+", remaining)
        if not m:
            break
        env_vars[m.group(1)] = m.group(2)
        remaining = remaining[m.end():]

    # Split into tokens
    try:
        tokens = shlex.split(remaining)
    except ValueError:
        tokens = remaining.split()

    executable = tokens[0] if tokens else ""
    args = tokens[1:] if len(tokens) > 1 else []

    # Extract redirects
    redirects: list[str] = []
    clean_args: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in (">", ">>", "2>", "2>>", "&>", "&>>") and i + 1 < len(args):
            redirects.append(f"{arg} {args[i + 1]}")
            i += 2
            continue
        if re.match(r"^[12]?>", arg):
            redirects.append(arg)
            i += 1
            continue
        clean_args.append(arg)
        i += 1

    return ParsedCommand(
        raw=command,
        executable=executable,
        args=clean_args,
        is_piped=False,
        is_background=is_bg,
        redirects=redirects,
        env_vars=env_vars,
    )


def _split_on_pipe(command: str) -> list[str]:
    """Split command on pipe operator, respecting quotes."""
    parts: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    i = 0

    while i < len(command):
        ch = command[i]
        if ch == "\\" and i + 1 < len(command):
            current.append(ch)
            current.append(command[i + 1])
            i += 2
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "|" and not in_single and not in_double:
            # Don't split on ||
            if i + 1 < len(command) and command[i + 1] == "|":
                current.append(ch)
                current.append(command[i + 1])
                i += 2
                continue
            parts.append("".join(current))
            current = []
            i += 1
            continue
        current.append(ch)
        i += 1

    if current:
        parts.append("".join(current))

    return parts


def _is_in_quotes(text: str, pos: int) -> bool:
    """Check if a position in text is inside quotes."""
    in_single = False
    in_double = False
    for i in range(pos):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
    return in_single or in_double
