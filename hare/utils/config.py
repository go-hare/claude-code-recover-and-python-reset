"""
Configuration management.

Port of: src/utils/config.ts
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Optional


@dataclass
class GlobalConfig:
    theme: str = "default"
    last_release_notes_seen: Optional[str] = None


@dataclass
class ProjectConfig:
    last_cost: Optional[float] = None
    last_duration: Optional[float] = None
    last_api_duration: Optional[float] = None
    last_tool_duration: Optional[float] = None
    last_session_id: Optional[str] = None
    last_lines_added: Optional[int] = None
    last_lines_removed: Optional[int] = None


_configs_enabled = False


def enable_configs() -> None:
    global _configs_enabled
    _configs_enabled = True


def _get_config_dir() -> str:
    home = os.path.expanduser("~")
    return os.path.join(home, ".claude")


def _load_json(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


@lru_cache(maxsize=1)
def get_global_config() -> GlobalConfig:
    data = _load_json(os.path.join(_get_config_dir(), "config.json"))
    return GlobalConfig(
        theme=data.get("theme", "default"),
        last_release_notes_seen=data.get("lastReleaseNotesSeen"),
    )


@lru_cache(maxsize=1)
def get_current_project_config() -> ProjectConfig:
    data = _load_json(os.path.join(_get_config_dir(), "project.json"))
    return ProjectConfig(
        last_cost=data.get("lastCost"),
        last_duration=data.get("lastDuration"),
    )
