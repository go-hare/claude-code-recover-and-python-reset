"""
Plugin installation manager.

Port of: src/services/plugins/PluginInstallationManager.ts

Handles background plugin installations and updates.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Optional

from hare.services.plugins.plugin_types import PluginConfig


async def perform_background_plugin_installations(
    plugins_to_install: list[PluginConfig],
    *,
    install_dir: str = "",
    on_progress: Optional[Any] = None,
) -> list[dict[str, Any]]:
    """
    Install multiple plugins in the background.

    Returns a list of results for each plugin.
    """
    results = []
    for plugin in plugins_to_install:
        try:
            result = await _install_single_plugin(plugin, install_dir=install_dir)
            results.append(result)
            if on_progress:
                on_progress(plugin.name, "installed")
        except Exception as e:
            results.append({
                "name": plugin.name,
                "status": "error",
                "error": str(e),
            })
            if on_progress:
                on_progress(plugin.name, "error")
    return results


async def _install_single_plugin(
    plugin: PluginConfig,
    *,
    install_dir: str = "",
) -> dict[str, Any]:
    """Install a single plugin."""
    # In a full implementation, this would:
    # 1. Download the plugin package
    # 2. Verify checksums
    # 3. Extract to install_dir
    # 4. Run post-install hooks
    return {
        "name": plugin.name,
        "version": plugin.version,
        "status": "installed",
        "source": plugin.source,
    }
