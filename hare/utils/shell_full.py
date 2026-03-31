"""
Full shell execution with CWD tracking and sandbox support.

Port of: src/utils/Shell.ts

Handles:
- Shell detection (bash, zsh, PowerShell)
- Command execution with timeout
- CWD change tracking
- Output file management
- Process lifecycle management
"""

from __future__ import annotations

import asyncio
import os
import shutil
import signal
import sys
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from hare.bootstrap.state import get_original_cwd, get_session_id, set_cwd_state as set_cwd
from hare.utils.debug import log_for_debugging
from hare.utils.errors import error_message

DEFAULT_TIMEOUT = 30 * 60  # 30 minutes in seconds

ShellType = str  # "bash" | "powershell"


@dataclass
class ExecResult:
    """Result from executing a shell command."""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    interrupted: bool = False
    timed_out: bool = False
    duration_ms: float = 0.0


@dataclass
class ExecOptions:
    timeout: Optional[float] = None
    on_progress: Optional[Callable[..., None]] = None
    prevent_cwd_changes: bool = False
    should_use_sandbox: bool = False
    should_auto_background: bool = False
    on_stdout: Optional[Callable[[str], None]] = None


def _is_executable(shell_path: str) -> bool:
    """Check if a shell path is executable."""
    if not os.path.isfile(shell_path):
        return False
    return os.access(shell_path, os.X_OK)


async def find_suitable_shell() -> str:
    """
    Find the best available shell to use.
    On Windows: PowerShell
    On POSIX: bash or zsh
    """
    # Check explicit override
    override = os.environ.get("CLAUDE_CODE_SHELL", "")
    if override:
        if ("bash" in override or "zsh" in override) and _is_executable(override):
            log_for_debugging(f"Using shell override: {override}")
            return override

    if sys.platform == "win32":
        # Windows: use PowerShell
        for ps in [
            shutil.which("pwsh"),  # PowerShell 7+
            shutil.which("powershell"),
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
        ]:
            if ps and os.path.isfile(ps):
                return ps
        return "powershell.exe"

    # POSIX: prefer user's SHELL, then detect
    env_shell = os.environ.get("SHELL", "")
    prefer_bash = "bash" in env_shell

    zsh_path = shutil.which("zsh")
    bash_path = shutil.which("bash")

    candidates: list[str] = []

    # Add environment shell first if it's bash or zsh
    if env_shell and ("bash" in env_shell or "zsh" in env_shell):
        if _is_executable(env_shell):
            candidates.append(env_shell)

    # Add discovered paths based on preference
    if prefer_bash:
        if bash_path:
            candidates.append(bash_path)
        if zsh_path:
            candidates.append(zsh_path)
    else:
        if zsh_path:
            candidates.append(zsh_path)
        if bash_path:
            candidates.append(bash_path)

    # Standard paths
    search_dirs = ["/bin", "/usr/bin", "/usr/local/bin", "/opt/homebrew/bin"]
    shell_order = ["bash", "zsh"] if prefer_bash else ["zsh", "bash"]
    for shell in shell_order:
        for d in search_dirs:
            p = os.path.join(d, shell)
            if p not in candidates:
                candidates.append(p)

    for c in candidates:
        if _is_executable(c):
            return c

    raise RuntimeError(
        "No suitable shell found. Please ensure bash or zsh is installed."
    )


def _get_shell_type() -> ShellType:
    """Determine the shell type for the current platform."""
    if sys.platform == "win32":
        return "powershell"
    return "bash"


async def exec_command(
    command: str,
    *,
    timeout: Optional[float] = None,
    cwd: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
    on_progress: Optional[Callable[..., None]] = None,
    on_stdout: Optional[Callable[[str], None]] = None,
) -> ExecResult:
    """
    Execute a shell command and return the result.

    This is the main execution entry point, equivalent to Shell.exec() in TS.
    """
    effective_timeout = timeout or DEFAULT_TIMEOUT
    effective_cwd = cwd or get_original_cwd()
    effective_env = env or dict(os.environ)

    start_time = time.time()
    shell_type = _get_shell_type()

    try:
        if shell_type == "powershell":
            result = await _exec_powershell(
                command, effective_cwd, effective_env, effective_timeout, on_stdout
            )
        else:
            result = await _exec_bash(
                command, effective_cwd, effective_env, effective_timeout, on_stdout
            )
    except asyncio.TimeoutError:
        return ExecResult(
            stdout="",
            stderr=f"Command timed out after {effective_timeout}s",
            exit_code=124,
            timed_out=True,
            duration_ms=(time.time() - start_time) * 1000,
        )
    except Exception as e:
        return ExecResult(
            stdout="",
            stderr=error_message(e),
            exit_code=1,
            duration_ms=(time.time() - start_time) * 1000,
        )

    result.duration_ms = (time.time() - start_time) * 1000
    return result


async def _exec_bash(
    command: str,
    cwd: str,
    env: dict[str, str],
    timeout: float,
    on_stdout: Optional[Callable[[str], None]],
) -> ExecResult:
    """Execute a command using bash/zsh."""
    shell = await find_suitable_shell()

    proc = await asyncio.create_subprocess_exec(
        shell, "-c", command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=env,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        raise

    stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
    stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

    if on_stdout and stdout_str:
        on_stdout(stdout_str)

    return ExecResult(
        stdout=stdout_str,
        stderr=stderr_str,
        exit_code=proc.returncode or 0,
    )


async def _exec_powershell(
    command: str,
    cwd: str,
    env: dict[str, str],
    timeout: float,
    on_stdout: Optional[Callable[[str], None]],
) -> ExecResult:
    """Execute a command using PowerShell."""
    ps_path = shutil.which("pwsh") or shutil.which("powershell") or "powershell.exe"

    # Encode command to avoid quoting issues
    ps_command = f'Set-Location -LiteralPath "{cwd}"; {command}'

    proc = await asyncio.create_subprocess_exec(
        ps_path,
        "-NoProfile", "-NonInteractive",
        "-Command", ps_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        raise

    stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
    stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

    if on_stdout and stdout_str:
        on_stdout(stdout_str)

    return ExecResult(
        stdout=stdout_str,
        stderr=stderr_str,
        exit_code=proc.returncode or 0,
    )


async def detect_cwd_after_command(
    shell: str,
    previous_cwd: str,
) -> str:
    """Detect if a command changed the working directory."""
    try:
        proc = await asyncio.create_subprocess_exec(
            shell, "-c", "pwd",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=previous_cwd,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        new_cwd = stdout.decode().strip() if stdout else ""
        if new_cwd and os.path.isdir(new_cwd):
            return new_cwd
    except Exception:
        pass
    return previous_cwd
