"""
Mode validation for bash commands.

Port of: src/tools/BashTool/modeValidation.ts
"""

from __future__ import annotations

from typing import Any, Optional

ACCEPT_EDITS_ALLOWED_COMMANDS = frozenset({
    "git", "npm", "yarn", "pnpm", "pip", "pip3", "python", "python3",
    "node", "cargo", "go", "make", "cmake", "mvn", "gradle",
    "dotnet", "ruby", "bundle", "gem", "composer", "php",
    "rustc", "javac", "gcc", "g++", "clang",
})


def check_permission_mode(
    command: str,
    mode: str,
) -> dict[str, Any]:
    """
    Check if a command is allowed in the given permission mode.

    Modes:
    - 'default': all commands allowed
    - 'plan': only read-only commands allowed
    - 'acceptEdits': only build/test/VCS commands allowed
    """
    if mode == "default":
        return {"allowed": True}

    if mode == "plan":
        return {"allowed": False, "reason": "Cannot execute commands in plan mode"}

    if mode == "acceptEdits":
        first_word = command.strip().split()[0] if command.strip() else ""
        if first_word in ACCEPT_EDITS_ALLOWED_COMMANDS:
            return {"allowed": True}
        return {
            "allowed": False,
            "reason": f"Command '{first_word}' not allowed in acceptEdits mode",
        }

    return {"allowed": True}


def get_auto_allowed_commands(mode: str) -> frozenset[str]:
    """Get the set of auto-allowed commands for a given mode."""
    if mode == "acceptEdits":
        return ACCEPT_EDITS_ALLOWED_COMMANDS
    return frozenset()
