"""
Settings source constants.

Port of: src/utils/settings/constants.ts
"""

from __future__ import annotations

from typing import Literal

SETTING_SOURCES: list[str] = [
    "userSettings",
    "projectSettings",
    "localSettings",
    "flagSettings",
    "policySettings",
]

SettingSource = Literal[
    "userSettings", "projectSettings", "localSettings",
    "flagSettings", "policySettings",
]

EditableSettingSource = Literal[
    "userSettings", "projectSettings", "localSettings",
]


def get_setting_source_name(source: SettingSource) -> str:
    names = {
        "userSettings": "user",
        "projectSettings": "project",
        "localSettings": "project, gitignored",
        "flagSettings": "cli flag",
        "policySettings": "managed",
    }
    return names.get(source, source)


def get_source_display_name(source: str) -> str:
    names = {
        "userSettings": "User",
        "projectSettings": "Project",
        "localSettings": "Local",
        "flagSettings": "Flag",
        "policySettings": "Managed",
        "plugin": "Plugin",
        "built-in": "Built-in",
    }
    return names.get(source, source)


def get_enabled_setting_sources() -> list[SettingSource]:
    """Get all enabled setting sources (policy and flag always included)."""
    return list(SETTING_SOURCES)  # type: ignore[arg-type]


def is_setting_source_enabled(source: SettingSource) -> bool:
    return source in get_enabled_setting_sources()


SOURCES: list[EditableSettingSource] = [
    "localSettings", "projectSettings", "userSettings",
]

CLAUDE_CODE_SETTINGS_SCHEMA_URL = (
    "https://json.schemastore.org/claude-code-settings.json"
)
