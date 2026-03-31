"""
/config command - open config panel.

Port of: src/commands/config/index.ts
"""

from __future__ import annotations

from typing import Any

from hare.utils.settings.settings import get_settings, get_settings_file_path_for_source

COMMAND_NAME = "config"
DESCRIPTION = "Open config panel"
ALIASES = ["settings"]


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /config command."""
    if args.strip():
        # Show specific setting
        key = args.strip()
        settings = get_settings()
        value = settings.get(key)
        if value is not None:
            return {"type": "text", "value": f"{key} = {value}"}
        return {"type": "text", "value": f"Setting '{key}' not found"}

    # Show all settings sources and current values
    lines = ["Settings:"]
    for source in ["userSettings", "projectSettings", "localSettings"]:
        path = get_settings_file_path_for_source(source)
        lines.append(f"  {source}: {path or 'not set'}")

    settings = get_settings()
    if settings:
        lines.append("\nCurrent settings:")
        for k, v in sorted(settings.items()):
            lines.append(f"  {k}: {v}")
    else:
        lines.append("\nNo settings configured.")

    return {"type": "text", "value": "\n".join(lines)}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "aliases": ALIASES,
        "call": call,
    }
