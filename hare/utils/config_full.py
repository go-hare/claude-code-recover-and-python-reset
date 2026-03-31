"""
Full configuration management.

Port of: src/utils/config.ts

Handles:
- Global config (read/write/cache)
- Project config
- Config file paths
- User ID generation
- Memory paths
- Config backup and migration
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional

from hare.bootstrap.state import get_cwd, get_session_id
from hare.utils.debug import log_for_debugging
from hare.utils.log import log_error_msg

# Config file paths
GLOBAL_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".claude")
GLOBAL_CONFIG_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.json")

EditorMode = Literal["vim", "emacs", "default"]
DiffTool = Literal["birddiff", "default"]
OutputStyle = Literal["text", "json", "stream-json"]
NotificationChannel = Literal["terminal", "iterm2", "terminal_bell"]
ReleaseChannel = Literal["stable", "beta"]
InstallMethod = Literal["npm", "standalone", "unknown"]


@dataclass
class ProjectConfig:
    """Per-project configuration."""
    allowed_tools: list[str] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    mcps: dict[str, Any] = field(default_factory=dict)


DEFAULT_PROJECT_CONFIG = ProjectConfig()


@dataclass
class GlobalConfig:
    """Global user configuration."""
    user_id: str = ""
    first_start_time: float = 0.0
    theme: str = "default"
    editor_mode: EditorMode = "default"
    diff_tool: DiffTool = "default"
    output_style: OutputStyle = "text"
    verbose: bool = False
    notification_channel: NotificationChannel = "terminal"
    release_channel: ReleaseChannel = "stable"
    auto_update: bool = True
    has_completed_onboarding: bool = False
    preferred_notification_mode: str = "auto"
    api_key: str = ""
    custom_api_url: str = ""
    install_method: InstallMethod = "unknown"
    pasted_content: list[dict[str, Any]] = field(default_factory=list)
    projects: dict[str, ProjectConfig] = field(default_factory=dict)
    num_starts: int = 0
    has_trust_dialog_accepted: bool = False
    trusted_paths: list[str] = field(default_factory=list)


DEFAULT_GLOBAL_CONFIG = GlobalConfig()


# Global config keys that appear at root level
GLOBAL_CONFIG_KEYS = {
    "user_id", "first_start_time", "theme", "editor_mode", "diff_tool",
    "output_style", "verbose", "notification_channel", "release_channel",
    "auto_update", "has_completed_onboarding", "preferred_notification_mode",
    "api_key", "custom_api_url", "install_method", "num_starts",
    "has_trust_dialog_accepted", "trusted_paths",
}

PROJECT_CONFIG_KEYS = {
    "allowed_tools", "history", "mcps",
}


# Cache for global config
_global_config_cache: Optional[dict[str, Any]] = None
_config_watchers_active = False


def _ensure_config_dir() -> None:
    """Ensure the global config directory exists."""
    os.makedirs(GLOBAL_CONFIG_DIR, mode=0o700, exist_ok=True)


def _sanitize_path(path: str) -> str:
    """Sanitize a path for use as a config key."""
    return path.replace(os.sep, "_").replace("/", "_").replace(":", "_").strip("_")


def get_config(path: Optional[str] = None) -> dict[str, Any]:
    """
    Read and parse a JSON config file.
    Returns empty dict on missing/corrupt file.
    """
    config_path = path or GLOBAL_CONFIG_PATH

    if not os.path.isfile(config_path):
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Strip BOM if present
        if content.startswith("\ufeff"):
            content = content[1:]
        return json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        log_error_msg(f"Config file corrupt: {config_path}: {e}")
        _backup_corrupt_config(config_path)
        return {}
    except OSError:
        return {}


def _backup_corrupt_config(config_path: str) -> None:
    """Back up a corrupt config file."""
    try:
        backup = f"{config_path}.backup.{int(time.time())}"
        os.rename(config_path, backup)
        log_for_debugging(f"Backed up corrupt config to {backup}")
    except OSError:
        pass


def save_config(config: dict[str, Any], path: Optional[str] = None) -> None:
    """Save config to a JSON file."""
    config_path = path or GLOBAL_CONFIG_PATH
    _ensure_config_dir()

    try:
        parent = os.path.dirname(config_path)
        os.makedirs(parent, mode=0o700, exist_ok=True)

        content = json.dumps(config, indent=2, ensure_ascii=False)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)
            f.write("\n")
    except OSError as e:
        log_error_msg(f"Failed to save config: {config_path}: {e}")


def save_config_with_lock(config: dict[str, Any], path: Optional[str] = None) -> None:
    """Save config with file locking (best-effort on Windows)."""
    save_config(config, path)


def get_global_config() -> dict[str, Any]:
    """Get the global config with caching."""
    global _global_config_cache
    if _global_config_cache is not None:
        return dict(_global_config_cache)
    _global_config_cache = get_config(GLOBAL_CONFIG_PATH)
    return dict(_global_config_cache)


def write_through_global_config_cache(key: str, value: Any) -> None:
    """Update a single key in the cached global config and persist."""
    global _global_config_cache
    config = get_global_config()
    config[key] = value
    _global_config_cache = config
    save_config(config, GLOBAL_CONFIG_PATH)


def save_global_config(config: dict[str, Any]) -> None:
    """Save the full global config."""
    global _global_config_cache
    _global_config_cache = config
    save_config(config, GLOBAL_CONFIG_PATH)


def enable_configs() -> None:
    """Enable config file watching and caching."""
    global _config_watchers_active
    _config_watchers_active = True
    # Pre-load cache
    get_global_config()


def check_has_trust_dialog_accepted(cwd: str) -> bool:
    """Check if user has accepted the trust dialog for a path."""
    config = get_global_config()
    if config.get("has_trust_dialog_accepted"):
        return True
    trusted = config.get("trusted_paths", [])
    return cwd in trusted


def is_path_trusted(path: str) -> bool:
    """Check if a path is trusted."""
    return check_has_trust_dialog_accepted(path)


def get_or_create_user_id() -> str:
    """Get or create a persistent user ID."""
    config = get_global_config()
    uid = config.get("user_id", "")
    if uid:
        return uid

    uid = str(uuid.uuid4())
    write_through_global_config_cache("user_id", uid)
    return uid


def record_first_start_time() -> None:
    """Record the first start time if not already set."""
    config = get_global_config()
    if not config.get("first_start_time"):
        write_through_global_config_cache("first_start_time", time.time())


def get_project_path_for_config(cwd: str) -> str:
    """Get the project config directory path."""
    return os.path.join(GLOBAL_CONFIG_DIR, "projects", _sanitize_path(cwd))


def get_current_project_config() -> dict[str, Any]:
    """Get the current project's configuration."""
    cwd = get_cwd()
    project_dir = get_project_path_for_config(cwd)
    config_path = os.path.join(project_dir, "config.json")
    return get_config(config_path)


def save_current_project_config(config: dict[str, Any]) -> None:
    """Save the current project's configuration."""
    cwd = get_cwd()
    project_dir = get_project_path_for_config(cwd)
    config_path = os.path.join(project_dir, "config.json")
    save_config(config, config_path)


def get_memory_path(cwd: str) -> str:
    """Get the memory file path for a project."""
    project_dir = get_project_path_for_config(cwd)
    return os.path.join(project_dir, "memory.md")


def get_managed_claude_rules_dir(cwd: str) -> str:
    """Get the managed Claude rules directory."""
    project_dir = get_project_path_for_config(cwd)
    return os.path.join(project_dir, "rules")


def get_user_claude_rules_dir() -> str:
    """Get the user's Claude rules directory."""
    return os.path.join(GLOBAL_CONFIG_DIR, "rules")
