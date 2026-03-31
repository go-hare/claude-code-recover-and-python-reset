"""
Plugin types.

Port of: src/types/plugin.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PluginPermission:
    tool_name: str
    description: str = ""


@dataclass
class PluginManifest:
    name: str
    version: str = "0.0.1"
    description: str = ""
    author: str = ""
    homepage: str = ""
    permissions: list[PluginPermission] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)
    mcp_servers: list[dict[str, Any]] = field(default_factory=list)
    commands: list[dict[str, str]] = field(default_factory=list)
    hooks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class InstalledPlugin:
    name: str
    path: str
    manifest: PluginManifest
    enabled: bool = True
    source: str = "local"
