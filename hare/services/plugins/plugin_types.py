"""
Plugin types.

Port of: src/services/plugins/types.ts + pluginOperations.ts types
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PluginConfig:
    """Configuration for a plugin."""
    name: str
    version: str = ""
    enabled: bool = True
    source: str = ""  # npm, git, local
    package_name: str = ""
    install_path: str = ""
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginManifest:
    """Plugin manifest (package.json or similar)."""
    name: str
    version: str = ""
    description: str = ""
    author: str = ""
    main: str = ""
    tools: list[dict[str, Any]] = field(default_factory=list)
    commands: list[dict[str, Any]] = field(default_factory=list)
    mcp_servers: dict[str, Any] = field(default_factory=dict)


@dataclass
class InstalledPlugin:
    """Represents an installed plugin."""
    config: PluginConfig
    manifest: Optional[PluginManifest] = None
    install_dir: str = ""
    is_valid: bool = True
    error: Optional[str] = None
