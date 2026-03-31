"""
PowerShell shell provider.

Port of: src/utils/shell/powershellProvider.ts
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional

from hare.utils.shell.shell_provider import ShellProvider, ShellResult


class PowerShellProvider(ShellProvider):
    def get_name(self) -> str:
        return "powershell"

    def get_command_prefix(self) -> list[str]:
        return ["powershell", "-NoProfile", "-NonInteractive", "-Command"]

    async def execute(
        self,
        command: str,
        *,
        cwd: str = "",
        timeout: float = 120.0,
        env: Optional[dict[str, str]] = None,
    ) -> ShellResult:
        try:
            full_env = {**os.environ, **(env or {})}
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-NonInteractive", "-Command", command,
                cwd=cwd or None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=full_env,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout,
            )
            return ShellResult(
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
            )
        except asyncio.TimeoutError:
            return ShellResult(stderr="Command timed out", exit_code=124, timed_out=True)
        except Exception as e:
            return ShellResult(stderr=str(e), exit_code=1)
