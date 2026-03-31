"""
Command registry and loading.

Port of: src/commands.ts

Loads all command sources (skills, plugins, workflows, built-in).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional

from hare.types.command import Command, LocalCommand, PromptCommand, get_command_name, is_command_enabled


# ---------------------------------------------------------------------------
# Built-in commands  (matching COMMANDS() in TS)
# ---------------------------------------------------------------------------


def _make_local(name: str, desc: str, aliases: list[str] | None = None) -> LocalCommand:
    return LocalCommand(type="local", name=name, description=desc, aliases=aliases or [])


def _make_prompt(name: str, desc: str, aliases: list[str] | None = None) -> PromptCommand:
    return PromptCommand(type="prompt", name=name, description=desc, aliases=aliases or [])


def _builtin_commands() -> list[Command]:
    """All built-in slash commands (matches COMMANDS() memoized function in TS)."""
    return [
        _make_local("clear", "Clear the conversation"),
        _make_local("compact", "Compact the conversation context"),
        _make_local("config", "Open the configuration"),
        _make_local("cost", "Show session cost"),
        _make_local("diff", "Show recent changes"),
        _make_local("doctor", "Run diagnostics"),
        _make_local("exit", "Exit the REPL"),
        _make_local("help", "Show available commands"),
        _make_local("memory", "Show or edit CLAUDE.md memory files"),
        _make_local("model", "Switch model"),
        _make_local("resume", "Resume a previous conversation"),
        _make_local("status", "Show session status"),
        _make_local("theme", "Change the theme"),
        _make_local("vim", "Toggle vim mode"),
        _make_prompt("review", "Review code changes"),
        _make_prompt("init", "Initialize a new project"),
    ]


@lru_cache(maxsize=1)
def _builtin_command_names() -> set[str]:
    return {
        name
        for cmd in _builtin_commands()
        for name in [cmd.name, *(cmd.aliases or [])]
    }


# ---------------------------------------------------------------------------
# Skill / Plugin loading (stubs – real impl would read from disk)
# ---------------------------------------------------------------------------


async def _get_skills(cwd: str) -> dict[str, list[Command]]:
    """Load skills from directories."""
    return {
        "skill_dir_commands": [],
        "plugin_skills": [],
        "bundled_skills": [],
        "builtin_plugin_skills": [],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_commands(cwd: str) -> list[Command]:
    """
    Returns commands available to the current user.

    In the TS source this merges:
    - bundled skills
    - builtin plugin skills
    - skill dir commands
    - workflow commands
    - plugin commands
    - plugin skills
    - built-in COMMANDS()
    """
    skills = await _get_skills(cwd)
    all_commands: list[Command] = [
        *skills["bundled_skills"],
        *skills["builtin_plugin_skills"],
        *skills["skill_dir_commands"],
        *skills["plugin_skills"],
        *_builtin_commands(),
    ]
    return [cmd for cmd in all_commands if is_command_enabled(cmd)]


def find_command(command_name: str, commands: list[Command]) -> Optional[Command]:
    """Find a command by name or alias."""
    for cmd in commands:
        if (
            cmd.name == command_name
            or get_command_name(cmd) == command_name
            or command_name in (cmd.aliases or [])
        ):
            return cmd
    return None


def has_command(command_name: str, commands: list[Command]) -> bool:
    return find_command(command_name, commands) is not None


def get_command(command_name: str, commands: list[Command]) -> Command:
    cmd = find_command(command_name, commands)
    if cmd is None:
        available = ", ".join(sorted(c.name for c in commands))
        raise ReferenceError(
            f"Command {command_name} not found. Available commands: {available}"
        )
    return cmd


async def get_slash_command_tool_skills(cwd: str) -> list[Command]:
    """
    Filter commands to include only skills. Skills are commands that provide
    specialized capabilities for the model to use.
    """
    all_commands = await get_commands(cwd)
    return [
        cmd
        for cmd in all_commands
        if cmd.type == "prompt"
        and cmd.source != "builtin"
        and (getattr(cmd, "has_user_specified_description", False) or getattr(cmd, "when_to_use", None))
    ]


def format_description_with_source(cmd: Command) -> str:
    """Formats a command's description with its source annotation for user-facing UI."""
    if cmd.type != "prompt":
        return cmd.description
    if getattr(cmd, "kind", None) == "workflow":
        return f"{cmd.description} (workflow)"
    if cmd.source == "plugin":
        return f"{cmd.description} (plugin)"
    if cmd.source in ("builtin", "mcp"):
        return cmd.description
    if cmd.source == "bundled":
        return f"{cmd.description} (bundled)"
    return cmd.description
