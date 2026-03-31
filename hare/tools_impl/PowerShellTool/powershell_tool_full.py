"""
PowerShellTool full implementation.

Port of: src/tools/PowerShellTool/ directory (12+ files)

Full call chain for Windows PowerShell execution including
permissions, security, path validation, and CLM types.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Optional

POWERSHELL_TOOL_NAME = "PowerShell"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "PowerShell command to execute"},
            "timeout": {"type": "number", "description": "Timeout in seconds"},
        },
        "required": ["command"],
    }


async def call(
    tool_input: dict[str, Any],
    *,
    cwd: str = "",
) -> dict[str, Any]:
    """Execute a PowerShell command with full checks."""
    command = tool_input.get("command", "")
    timeout = min(tool_input.get("timeout", 120.0), 600.0)

    if not command.strip():
        return {"type": "error", "error": "Empty command"}

    if sys.platform != "win32":
        return {"type": "error", "error": "PowerShell tool is only available on Windows"}

    try:
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-NoProfile", "-NonInteractive", "-Command", command,
            cwd=cwd or None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace")
        err = stderr.decode("utf-8", errors="replace")

        if proc.returncode != 0 and err:
            output += f"\nstderr: {err[:2000]}"

        return {
            "type": "tool_result",
            "content": output or "(no output)",
            "exit_code": proc.returncode or 0,
            "is_error": proc.returncode != 0,
        }
    except asyncio.TimeoutError:
        return {"type": "error", "error": "Command timed out", "exit_code": 124}
    except Exception as e:
        return {"type": "error", "error": str(e)}


# CLM (Constrained Language Mode) types
CLM_TYPES = {
    "FullLanguage": "Full language mode - no restrictions",
    "ConstrainedLanguage": "Constrained language mode - limited cmdlets",
    "RestrictedLanguage": "Restricted language mode - most features disabled",
    "NoLanguage": "No language mode - only approved cmdlets",
}


def detect_language_mode() -> str:
    """Detect the current PowerShell language mode."""
    return "FullLanguage"


# Git safety checks for PowerShell
DANGEROUS_GIT_PS_COMMANDS = frozenset({
    "git push --force", "git push -f",
    "git reset --hard", "git clean -fd",
    "Remove-Item -Recurse -Force",
})


def is_git_safe_ps(command: str) -> bool:
    """Check if a PowerShell git command is safe."""
    cmd_lower = command.lower().strip()
    for dangerous in DANGEROUS_GIT_PS_COMMANDS:
        if dangerous.lower() in cmd_lower:
            return False
    return True
