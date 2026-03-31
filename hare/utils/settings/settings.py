"""
Settings management.

Port of: src/utils/settings/settings.ts

Loads and merges settings from multiple sources with caching.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from hare.utils.settings.types import SettingsJson
from hare.utils.settings.constants import SettingSource, SETTING_SOURCES


_settings_cache: dict[str, Optional[SettingsJson]] = {}


def get_settings(project_dir: str = "") -> SettingsJson:
    """Get merged settings from all sources."""
    merged: SettingsJson = {}
    for source in SETTING_SOURCES:
        source_settings = get_settings_for_source(source, project_dir=project_dir)
        if source_settings:
            _merge_settings(merged, source_settings)
    return merged


def get_settings_for_source(
    source: SettingSource,
    project_dir: str = "",
) -> Optional[SettingsJson]:
    """Get settings for a specific source."""
    path = get_settings_file_path_for_source(source, project_dir=project_dir)
    if not path:
        return None
    result = parse_settings_file(path)
    return result.get("settings")


def parse_settings_file(path: str) -> dict[str, Any]:
    """Parse a settings file and return settings + errors."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            return {"settings": {}, "errors": []}
        data = json.loads(content)
        if not isinstance(data, dict):
            return {"settings": None, "errors": [{"message": "Settings must be a JSON object"}]}
        return {"settings": data, "errors": []}
    except FileNotFoundError:
        return {"settings": None, "errors": []}
    except json.JSONDecodeError as e:
        return {"settings": None, "errors": [{"message": f"Invalid JSON: {e}"}]}


def get_settings_file_path_for_source(
    source: SettingSource,
    project_dir: str = "",
) -> Optional[str]:
    """Get the file path for a settings source."""
    if source == "userSettings":
        home = os.path.expanduser("~")
        return os.path.join(home, ".claude", "settings.json")
    elif source == "projectSettings":
        if not project_dir:
            return None
        return os.path.join(project_dir, ".claude", "settings.json")
    elif source == "localSettings":
        if not project_dir:
            return None
        return os.path.join(project_dir, ".claude", "settings.local.json")
    elif source == "policySettings":
        return _get_managed_settings_path()
    elif source == "flagSettings":
        return None  # Provided via CLI flag at runtime
    return None


def update_settings_for_source(
    source: SettingSource,
    updates: dict[str, Any],
    project_dir: str = "",
) -> None:
    """Update settings for a specific source."""
    path = get_settings_file_path_for_source(source, project_dir=project_dir)
    if not path:
        return
    current = parse_settings_file(path).get("settings") or {}
    current.update(updates)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)


def reset_settings_cache() -> None:
    """Clear the settings cache."""
    _settings_cache.clear()


def _merge_settings(target: SettingsJson, source: SettingsJson) -> None:
    """Merge source settings into target (source wins)."""
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            target[key].update(value)
        elif isinstance(value, list) and isinstance(target.get(key), list):
            target[key] = value  # Later source replaces arrays
        else:
            target[key] = value


def _get_managed_settings_path() -> str:
    """Get the managed settings file path based on platform."""
    import sys
    if sys.platform == "darwin":
        return "/Library/Application Support/ClaudeCode/managed-settings.json"
    elif sys.platform == "win32":
        return os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"),
                           "ClaudeCode", "managed-settings.json")
    else:
        return "/etc/claude-code/managed-settings.json"
