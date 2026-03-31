"""
BashTool main execution logic.

Port of: src/tools/BashTool/BashTool.tsx (main call chain)

Full call chain: validate → check permissions → security classify →
execute command → process output → return result.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Optional

from hare.tools_impl.BashTool.bash_permissions import check_bash_permission
from hare.tools_impl.BashTool.bash_security import classify_command_risk
from hare.tools_impl.BashTool.command_semantics import interpret_command_result
from hare.tools_impl.BashTool.destructive_command_warning import get_destructive_command_warning
from hare.tools_impl.BashTool.mode_validation import check_permission_mode
from hare.tools_impl.BashTool.path_validation import check_path_constraints
from hare.utils.shell.output_limits import truncate_output, get_output_limit

BASH_TOOL_NAME = "Bash"
DEFAULT_TIMEOUT = 120.0
MAX_TIMEOUT = 600.0


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute",
            },
            "timeout": {
                "type": "number",
                "description": "Timeout in seconds (max 600)",
            },
            "description": {
                "type": "string",
                "description": "Short description of the command's purpose",
            },
        },
        "required": ["command"],
    }


async def call(
    tool_input: dict[str, Any],
    *,
    cwd: str = "",
    permission_mode: str = "default",
    env: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Execute a bash command with full permission/security checks."""
    command = tool_input.get("command", "")
    timeout = min(tool_input.get("timeout", DEFAULT_TIMEOUT), MAX_TIMEOUT)
    description = tool_input.get("description", "")

    if not command.strip():
        return {"type": "error", "error": "Empty command"}

    # Mode validation
    mode_result = check_permission_mode(command, permission_mode)
    mode_error = mode_result.get("error") if isinstance(mode_result, dict) else None
    if mode_error:
        return {"type": "error", "error": mode_error}

    # Security classification
    security = {"risk": classify_command_risk(command)}

    # Destructive command check
    destructive_warning = get_destructive_command_warning(command)
    if destructive_warning:
        security["is_destructive"] = True

    # Path validation
    path_result = check_path_constraints(command, cwd or ".")
    path_error = path_result.get("error") if isinstance(path_result, dict) else None
    if path_error:
        return {"type": "error", "error": path_error}

    # Permission check
    perm_result = check_bash_permission(command, mode=permission_mode)
    if not perm_result.get("allowed", False):
        return {
            "type": "permission_denied",
            "error": perm_result.get("reason", "Permission denied"),
            "command": command,
        }

    # Execute
    try:
        result = await _execute_command(command, cwd=cwd, timeout=timeout, env=env)
    except Exception as e:
        return {"type": "error", "error": str(e)}

    # Process output
    stdout = truncate_output(result.get("stdout", ""), get_output_limit())
    stderr = result.get("stderr", "")
    exit_code = result.get("exit_code", 0)

    semantics = interpret_command_result(command, exit_code)

    output_parts = []
    if stdout:
        output_parts.append(stdout)
    if stderr and exit_code != 0:
        output_parts.append(f"stderr: {stderr[:2000]}")
    output = "\n".join(output_parts) if output_parts else "(no output)"

    return {
        "type": "tool_result",
        "content": output,
        "exit_code": exit_code,
        "is_error": exit_code != 0,
        "timed_out": result.get("timed_out", False),
        "semantics": semantics,
    }


async def _execute_command(
    command: str,
    *,
    cwd: str = "",
    timeout: float = DEFAULT_TIMEOUT,
    env: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Execute a command via subprocess."""
    full_env = {**os.environ, **(env or {})}

    if sys.platform == "win32":
        shell_cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", command]
    else:
        shell_cmd = ["bash", "-c", command]

    try:
        proc = await asyncio.create_subprocess_exec(
            *shell_cmd,
            cwd=cwd or None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=full_env,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout,
        )
        return {
            "stdout": stdout_bytes.decode("utf-8", errors="replace"),
            "stderr": stderr_bytes.decode("utf-8", errors="replace"),
            "exit_code": proc.returncode or 0,
            "timed_out": False,
        }
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        return {
            "stdout": "",
            "stderr": "Command timed out",
            "exit_code": 124,
            "timed_out": True,
        }
