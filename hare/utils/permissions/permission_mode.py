"""
Permission mode configuration.

Port of: src/utils/permissions/PermissionMode.ts
"""

from __future__ import annotations

from typing import Literal, Optional

from hare.types.permissions import (
    EXTERNAL_PERMISSION_MODES,
    ExternalPermissionMode,
    PERMISSION_MODES,
    PermissionMode,
)

PAUSE_ICON = "||"

PermissionModeConfig = dict


_MODE_CONFIGS: dict[str, PermissionModeConfig] = {
    "default": {
        "title": "Default",
        "short_title": "Default",
        "symbol": "",
        "color": "text",
        "external": "default",
    },
    "plan": {
        "title": "Plan Mode",
        "short_title": "Plan",
        "symbol": PAUSE_ICON,
        "color": "planMode",
        "external": "plan",
    },
    "acceptEdits": {
        "title": "Accept edits",
        "short_title": "Accept",
        "symbol": ">>",
        "color": "autoAccept",
        "external": "acceptEdits",
    },
    "bypassPermissions": {
        "title": "Bypass Permissions",
        "short_title": "Bypass",
        "symbol": ">>",
        "color": "error",
        "external": "bypassPermissions",
    },
    "dontAsk": {
        "title": "Don't Ask",
        "short_title": "DontAsk",
        "symbol": ">>",
        "color": "error",
        "external": "dontAsk",
    },
    "auto": {
        "title": "Auto mode",
        "short_title": "Auto",
        "symbol": ">>",
        "color": "warning",
        "external": "default",
    },
}


def _get_mode_config(mode: str) -> PermissionModeConfig:
    return _MODE_CONFIGS.get(mode, _MODE_CONFIGS["default"])


def is_external_permission_mode(mode: str) -> bool:
    return mode not in ("auto", "bubble")


def to_external_permission_mode(mode: str) -> ExternalPermissionMode:
    return _get_mode_config(mode).get("external", "default")


def permission_mode_from_string(s: str) -> PermissionMode:
    if s in PERMISSION_MODES:
        return s  # type: ignore[return-value]
    return "default"


def permission_mode_title(mode: str) -> str:
    return _get_mode_config(mode).get("title", "Default")


def is_default_mode(mode: Optional[str]) -> bool:
    return mode == "default" or mode is None


def permission_mode_short_title(mode: str) -> str:
    return _get_mode_config(mode).get("short_title", "Default")


def permission_mode_symbol(mode: str) -> str:
    return _get_mode_config(mode).get("symbol", "")
