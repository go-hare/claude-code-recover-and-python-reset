"""
Read-only command validation.

Port of: src/utils/shell/readOnlyCommandValidation.ts
"""

from __future__ import annotations

import re

READ_ONLY_COMMANDS = frozenset({
    "ls", "cat", "head", "tail", "find", "grep", "rg",
    "wc", "file", "stat", "du", "df", "pwd", "whoami",
    "which", "where", "type", "echo", "env", "printenv",
    "git log", "git status", "git diff", "git show",
    "git branch", "git remote", "git tag",
    "python --version", "python3 --version",
    "node --version", "npm --version",
    "pip list", "pip show", "pip freeze",
})


def is_read_only_command(command: str) -> bool:
    """Check if a command is read-only (safe to run without permission)."""
    cmd = command.strip()
    for ro_cmd in READ_ONLY_COMMANDS:
        if cmd == ro_cmd or cmd.startswith(ro_cmd + " "):
            return True
    return False
