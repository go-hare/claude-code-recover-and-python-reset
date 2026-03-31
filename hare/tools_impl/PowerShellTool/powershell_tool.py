"""
PowerShell Tool - execute PowerShell commands on Windows.

Port of: src/tools/PowerShellTool/PowerShellTool.tsx

This tool runs PowerShell commands on Windows systems, with the same
permission model and security checks as BashTool for Unix systems.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
from typing import Any, Optional

TOOL_NAME = "PowerShell"
DESCRIPTION = "Execute a PowerShell command on Windows"
PROMPT = """Runs a PowerShell command in a PowerShell session on Windows.

Important notes:
- Use this tool for system commands on Windows
- PowerShell has different syntax from bash (e.g., Get-ChildItem instead of ls)
- Commands run in a non-interactive session
- Use proper PowerShell cmdlets and syntax"""


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The PowerShell command to execute",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in milliseconds (default: 120000)",
            },
        },
        "required": ["command"],
    }


async def call(
    command: str,
    timeout: int = 120_000,
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a PowerShell command."""
    if sys.platform != "win32":
        return {
            "stdout": "",
            "stderr": "PowerShell tool is only available on Windows",
            "exit_code": 1,
        }

    ps_path = shutil.which("pwsh") or shutil.which("powershell") or "powershell.exe"
    timeout_sec = timeout / 1000

    try:
        proc = await asyncio.create_subprocess_exec(
            ps_path,
            "-NoProfile", "-NonInteractive",
            "-Command", command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_sec
        )
        return {
            "stdout": stdout.decode("utf-8", errors="replace") if stdout else "",
            "stderr": stderr.decode("utf-8", errors="replace") if stderr else "",
            "exit_code": proc.returncode or 0,
        }
    except asyncio.TimeoutError:
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout_sec}s",
            "exit_code": 124,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": 1,
        }
