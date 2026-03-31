"""
Sandbox adapter.

Port of: src/utils/sandbox/sandbox-adapter.ts

Bridge between external sandbox runtime and CLI settings/tool integration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SandboxConfig:
    enabled: bool = False
    filesystem_allow_write: list[str] = field(default_factory=list)
    filesystem_deny_write: list[str] = field(default_factory=list)
    network_allow: list[str] = field(default_factory=list)
    network_deny: list[str] = field(default_factory=list)


def resolve_path_pattern_for_sandbox(
    pattern: str,
    source: str = "user",
    settings_root: str = "",
) -> str:
    """Resolve Claude Code-specific path patterns for sandbox-runtime."""
    if pattern.startswith("//"):
        return pattern[1:]
    if pattern.startswith("/") and not pattern.startswith("//"):
        root = settings_root or os.getcwd()
        return os.path.join(root, pattern[1:])
    return pattern


def resolve_sandbox_filesystem_path(
    pattern: str,
    source: str = "user",
    settings_root: str = "",
) -> str:
    """Resolve paths from sandbox.filesystem.* settings."""
    if pattern.startswith("//"):
        return pattern[1:]
    return os.path.expanduser(pattern) if pattern.startswith("~") else pattern


class SandboxManager:
    """Manages sandbox execution environment."""

    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        self._config = config or SandboxConfig()
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    def start(self) -> None:
        if self._config.enabled:
            self._active = True

    def stop(self) -> None:
        self._active = False

    def is_path_allowed_write(self, path: str) -> bool:
        if not self._active:
            return True
        abs_path = os.path.abspath(path)
        for deny in self._config.filesystem_deny_write:
            if abs_path.startswith(deny):
                return False
        if self._config.filesystem_allow_write:
            return any(abs_path.startswith(a) for a in self._config.filesystem_allow_write)
        return True

    def is_network_allowed(self, host: str) -> bool:
        if not self._active:
            return True
        for deny in self._config.network_deny:
            if host == deny or host.endswith("." + deny):
                return False
        if self._config.network_allow:
            return any(host == a or host.endswith("." + a) for a in self._config.network_allow)
        return True


def get_sandbox_config() -> SandboxConfig:
    """Get sandbox configuration from settings."""
    return SandboxConfig()
