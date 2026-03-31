"""
Config Tool - read/write configuration settings.

Port of: src/tools/ConfigTool/ConfigTool.ts
"""

from __future__ import annotations

from typing import Any

from hare.utils.config_full import get_global_config, write_through_global_config_cache

TOOL_NAME = "Config"
DESCRIPTION = "Read or update configuration settings"
PROMPT = """Use this tool to read or modify Claude Code configuration settings."""

SUPPORTED_SETTINGS = [
    "theme", "editor_mode", "verbose", "notification_channel",
    "auto_update", "output_style",
]


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get", "set", "list"],
                "description": "Action to perform",
            },
            "key": {"type": "string", "description": "Setting key"},
            "value": {"type": "string", "description": "Setting value (for set)"},
        },
        "required": ["action"],
    }


async def call(
    action: str,
    key: str = "",
    value: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    if action == "list":
        config = get_global_config()
        return {"settings": {k: config.get(k) for k in SUPPORTED_SETTINGS}}

    if action == "get":
        if not key:
            return {"error": "key is required for get"}
        config = get_global_config()
        return {"key": key, "value": config.get(key)}

    if action == "set":
        if not key or not value:
            return {"error": "key and value are required for set"}
        if key not in SUPPORTED_SETTINGS:
            return {"error": f"Unknown setting: {key}. Supported: {SUPPORTED_SETTINGS}"}
        write_through_global_config_cache(key, value)
        return {"key": key, "value": value, "status": "updated"}

    return {"error": f"Unknown action: {action}"}
