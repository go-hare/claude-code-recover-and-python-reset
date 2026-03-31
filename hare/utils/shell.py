"""
Shell execution utilities.

Port of: src/utils/Shell.ts

Provides shell command execution with timeout, sandbox support,
and working directory tracking.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from hare.utils.cwd import get_cwd, set_cwd

DEFAULT_TIMEOUT = 30 * 60  # 30 minutes in seconds


@dataclass
class ExecResult:
    """Result of a shell command execution."""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    timed_out: bool = False
    background_task_id: Optional[str] = None


@dataclass
class ShellConfig:
    """Shell configuration."""
    shell_path: str = ""
    shell_type: str = "bash"


async def find_suitable_shell() -> str:
    """
    Determine the best available shell to use.
    Mirrors findSuitableShell() from Shell.ts.
    """
    # Check explicit override
    shell_override = os.environ.get("CLAUDE_CODE_SHELL")
    if shell_override and _is_executable(shell_override):
        return shell_override

    # On Windows, use PowerShell
    if os.name == "nt":
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        if pwsh:
            return pwsh
        return "powershell"

    # On POSIX, check SHELL env then try common shells
    env_shell = os.environ.get("SHELL", "")
    prefer_bash = "bash" in env_shell

    # Try user's preferred shell first
    if env_shell and _is_executable(env_shell):
        return env_shell

    # Search for shells
    shell_order = ["bash", "zsh"] if prefer_bash else ["zsh", "bash"]

    for shell_name in shell_order:
        path = shutil.which(shell_name)
        if path:
            return path

    # Fallback paths
    fallback_paths = ["/bin/bash", "/usr/bin/bash", "/bin/zsh", "/usr/bin/zsh"]
    for path in fallback_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    raise RuntimeError(
        "No suitable shell found. "
        "Please ensure you have a valid shell installed."
    )


def _is_executable(path: str) -> bool:
    """Check if a path is executable."""
    try:
        return os.path.isfile(path) and os.access(path, os.X_OK)
    except OSError:
        return False


async def exec_command(
    command: str,
    *,
    timeout: Optional[float] = None,
    on_progress: Optional[Callable[[str, str, int, int, bool], None]] = None,
    prevent_cwd_changes: bool = False,
) -> ExecResult:
    """
    Execute a shell command.

    Mirrors exec() from Shell.ts with simplified implementation.
    """
    command_timeout = timeout or DEFAULT_TIMEOUT
    cwd = get_cwd()

    # Verify CWD exists
    if not os.path.isdir(cwd):
        return ExecResult(
            stderr=f'Working directory "{cwd}" no longer exists.',
            exit_code=1,
        )

    try:
        shell_path = await find_suitable_shell()
    except RuntimeError as e:
        return ExecResult(stderr=str(e), exit_code=126)

    # Build command
    if os.name == "nt":
        shell_args = [shell_path, "-Command", command]
    else:
        shell_args = [shell_path, "-c", command]

    env = {
        **os.environ,
        "GIT_EDITOR": "true",
        "CLAUDECODE": "1",
    }

    try:
        proc = await asyncio.create_subprocess_exec(
            *shell_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=command_timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return ExecResult(
                stderr=f"Command timed out after {command_timeout}s",
                exit_code=124,
                timed_out=True,
            )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        exit_code = proc.returncode or 0

        return ExecResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
        )

    except FileNotFoundError:
        return ExecResult(
            stderr=f"Shell not found: {shell_path}",
            exit_code=126,
        )
    except Exception as e:
        return ExecResult(
            stderr=str(e),
            exit_code=126,
        )
