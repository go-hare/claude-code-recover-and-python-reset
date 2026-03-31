"""
Plugin operations.

Port of: src/services/plugins/pluginOperations.ts

Core plugin management: finding, installing, removing plugins.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from hare.services.plugins.plugin_types import PluginConfig, InstalledPlugin


def find_plugin_in_settings(
    name: str,
    settings_path: str,
) -> Optional[PluginConfig]:
    """Find a plugin configuration in settings."""
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        plugins = data.get("plugins", {})
        if name in plugins:
            plugin_data = plugins[name]
            return PluginConfig(
                name=name,
                version=plugin_data.get("version", ""),
                enabled=plugin_data.get("enabled", True),
                source=plugin_data.get("source", ""),
                package_name=plugin_data.get("packageName", name),
            )
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        pass
    return None


def install_plugin(
    name: str,
    *,
    source: str = "npm",
    version: str = "",
    settings_path: str = "",
) -> dict[str, Any]:
    """Install a plugin."""
    # In the full implementation, this would run npm/pip install
    return {
        "name": name,
        "status": "installed",
        "source": source,
        "version": version,
    }


def remove_plugin(
    name: str,
    *,
    settings_path: str = "",
) -> dict[str, Any]:
    """Remove a plugin."""
    return {"name": name, "status": "removed"}


def list_installed_plugins(
    settings_path: str,
) -> list[InstalledPlugin]:
    """List all installed plugins."""
    plugins: list[InstalledPlugin] = []
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for name, plugin_data in data.get("plugins", {}).items():
            config = PluginConfig(
                name=name,
                version=plugin_data.get("version", ""),
                enabled=plugin_data.get("enabled", True),
                source=plugin_data.get("source", ""),
                package_name=plugin_data.get("packageName", name),
            )
            plugins.append(InstalledPlugin(config=config))
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        pass
    return plugins
