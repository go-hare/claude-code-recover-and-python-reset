"""
Shell provider interface.

Port of: src/utils/shell/shellProvider.ts
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ShellResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    timed_out: bool = False


class ShellProvider(ABC):
    """Base class for shell execution providers."""

    @abstractmethod
    def get_name(self) -> str:
        ...

    @abstractmethod
    def get_command_prefix(self) -> list[str]:
        ...

    @abstractmethod
    async def execute(
        self,
        command: str,
        *,
        cwd: str = "",
        timeout: float = 120.0,
        env: Optional[dict[str, str]] = None,
    ) -> ShellResult:
        ...

    def wrap_command(self, command: str) -> list[str]:
        return self.get_command_prefix() + [command]
