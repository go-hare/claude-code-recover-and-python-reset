"""
Command implementations registry.

Port of: src/commands/ directory

Discovers and registers all /slash command implementations.
"""

from __future__ import annotations

import importlib
from typing import Any, Optional

_COMMAND_MODULES = [
    "compact", "config_cmd", "memory", "permissions", "doctor",
    "help_cmd", "version", "clear", "cost", "diff_cmd", "usage",
    "model_cmd", "resume", "mcp", "status", "upgrade", "init_cmd",
    "skills_cmd", "session_cmd", "hooks_cmd", "plan_cmd",
    # New batch
    "color", "export_cmd", "rename", "rewind", "files", "stats",
    "branch", "commit", "login", "logout", "feedback", "context",
    "copy", "discover", "effort", "todo", "stash", "pr", "issue",
    "review", "search", "agent_cmd", "output_style", "worktree",
    "listen", "terminal", "vim", "theme",
]


def get_all_command_definitions() -> list[dict[str, Any]]:
    """Get all registered command definitions."""
    commands: list[dict[str, Any]] = []
    for mod_name in _COMMAND_MODULES:
        try:
            mod = importlib.import_module(f"hare.commands_impl.{mod_name}")
            commands.append({
                "name": getattr(mod, "COMMAND_NAME", mod_name),
                "description": getattr(mod, "DESCRIPTION", ""),
                "aliases": getattr(mod, "ALIASES", []),
                "call": getattr(mod, "call"),
            })
        except (ImportError, AttributeError):
            continue
    return commands


def find_command(name: str) -> Optional[dict[str, Any]]:
    """Find a command by name or alias."""
    name = name.lower().lstrip("/")
    for cmd in get_all_command_definitions():
        if cmd["name"] == name:
            return cmd
        if name in cmd.get("aliases", []):
            return cmd
    return None
