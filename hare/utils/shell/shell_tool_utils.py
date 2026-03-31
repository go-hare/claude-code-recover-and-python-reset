"""
Shell tool utilities.

Port of: src/utils/shell/shellToolUtils.ts
"""

from __future__ import annotations

import sys

SHELL_TOOL_NAMES = frozenset({"Bash", "PowerShell"})


def get_shell_tool_name() -> str:
    """Get the appropriate shell tool name for this platform."""
    if sys.platform == "win32":
        return "PowerShell"
    return "Bash"


def is_shell_tool(tool_name: str) -> bool:
    """Check if a tool name is a shell tool."""
    return tool_name in SHELL_TOOL_NAMES
